"""
数据库模块
使用 SQLite 存储用户积分、警告等数据
"""
import sqlite3
import os
import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

DB_PATH = "bot_data.db"


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接（优化：使用连接池和超时设置）"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=10.0,  # 10秒超时
            check_same_thread=False  # 允许多线程
        )
        # 优化设置
        conn.execute("PRAGMA journal_mode=WAL")  # 使用WAL模式提高并发性能
        conn.execute("PRAGMA synchronous=NORMAL")  # 平衡性能和安全性
        conn.execute("PRAGMA cache_size=10000")  # 增加缓存大小
        return conn
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 用户积分表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_points (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                points INTEGER DEFAULT 0,
                last_message_time INTEGER,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        
        # 警告记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                reason TEXT,
                timestamp INTEGER NOT NULL
            )
        """)
        
        # 积分历史记录表（可选，用于记录积分变化）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS points_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                points_change INTEGER NOT NULL,
                reason TEXT,
                timestamp INTEGER NOT NULL
            )
        """)
        
        # 群组设置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id INTEGER PRIMARY KEY,
                welcome_message TEXT,
                rules TEXT,
                auto_delete_ads INTEGER DEFAULT 1,
                welcome_new_members INTEGER DEFAULT 1,
                auto_kick_bots INTEGER DEFAULT 0,
                created_at INTEGER,
                updated_at INTEGER
            )
        """)
        
        # 创建索引以提高查询性能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_points 
            ON user_points(chat_id, user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_warnings 
            ON warnings(chat_id, user_id)
        """)
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")
    
    # ========== 积分相关方法 ==========
    
    def get_user_points(self, chat_id: int, user_id: int) -> int:
        """获取用户积分"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT points FROM user_points 
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def add_points(self, chat_id: int, user_id: int, points: int, reason: str = None) -> int:
        """增加用户积分"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 先检查用户是否存在
        cursor.execute("""
            SELECT points FROM user_points 
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        
        result = cursor.fetchone()
        
        if result:
            # 更新积分
            new_points = result[0] + points
            cursor.execute("""
                UPDATE user_points 
                SET points = ? 
                WHERE chat_id = ? AND user_id = ?
            """, (new_points, chat_id, user_id))
        else:
            # 创建新记录
            new_points = points
            cursor.execute("""
                INSERT INTO user_points (chat_id, user_id, points)
                VALUES (?, ?, ?)
            """, (chat_id, user_id, new_points))
        
        # 记录积分历史
        import time
        cursor.execute("""
            INSERT INTO points_history (chat_id, user_id, points_change, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (chat_id, user_id, points, reason or "系统", int(time.time())))
        
        conn.commit()
        conn.close()
        
        logger.info(f"用户 {user_id} 在群组 {chat_id} 获得 {points} 积分，当前积分: {new_points}")
        return new_points
    
    def subtract_points(self, chat_id: int, user_id: int, points: int, reason: str = None) -> int:
        """减少用户积分"""
        return self.add_points(chat_id, user_id, -points, reason)
    
    def set_points(self, chat_id: int, user_id: int, points: int) -> int:
        """设置用户积分（覆盖）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT points FROM user_points 
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        
        result = cursor.fetchone()
        
        if result:
            old_points = result[0]
            cursor.execute("""
                UPDATE user_points 
                SET points = ? 
                WHERE chat_id = ? AND user_id = ?
            """, (points, chat_id, user_id))
        else:
            old_points = 0
            cursor.execute("""
                INSERT INTO user_points (chat_id, user_id, points)
                VALUES (?, ?, ?)
            """, (chat_id, user_id, points))
        
        # 记录积分变化
        import time
        points_change = points - old_points
        cursor.execute("""
            INSERT INTO points_history (chat_id, user_id, points_change, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (chat_id, user_id, points_change, "管理员设置", int(time.time())))
        
        conn.commit()
        conn.close()
        
        logger.info(f"用户 {user_id} 在群组 {chat_id} 积分设置为 {points}")
        return points
    
    def get_top_users(self, chat_id: int, limit: int = 10) -> List[Tuple[int, int]]:
        """获取积分排行榜（返回 (user_id, points) 列表）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, points FROM user_points 
            WHERE chat_id = ? 
            ORDER BY points DESC 
            LIMIT ?
        """, (chat_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_user_rank(self, chat_id: int, user_id: int) -> Optional[int]:
        """获取用户排名（返回排名，1为最高）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 获取用户积分
        user_points = self.get_user_points(chat_id, user_id)
        
        # 计算排名（有多少人积分更高）
        cursor.execute("""
            SELECT COUNT(*) FROM user_points 
            WHERE chat_id = ? AND points > ?
        """, (chat_id, user_points))
        
        rank = cursor.fetchone()[0] + 1  # +1 因为排名从1开始
        conn.close()
        
        return rank if user_points > 0 else None
    
    def update_last_message_time(self, chat_id: int, user_id: int):
        """更新用户最后发言时间（用于防刷分）"""
        import time
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user_points 
            SET last_message_time = ? 
            WHERE chat_id = ? AND user_id = ?
        """, (int(time.time()), chat_id, user_id))
        
        conn.commit()
        conn.close()
    
    def can_earn_points(self, chat_id: int, user_id: int, cooldown: int = 60) -> bool:
        """检查用户是否可以获得积分（防刷分，冷却时间）"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT last_message_time FROM user_points 
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return True
        
        import time
        last_time = result[0]
        current_time = int(time.time())
        
        return (current_time - last_time) >= cooldown
    
    # ========== 警告相关方法 ==========
    
    def add_warning(self, chat_id: int, user_id: int, admin_id: int, reason: str = None) -> int:
        """添加警告记录"""
        import time
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO warnings (chat_id, user_id, admin_id, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (chat_id, user_id, admin_id, reason, int(time.time())))
        
        conn.commit()
        conn.close()
        
        # 返回警告总数
        return self.get_warning_count(chat_id, user_id)
    
    def get_warning_count(self, chat_id: int, user_id: int) -> int:
        """获取用户警告次数"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM warnings 
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def clear_warnings(self, chat_id: int, user_id: int) -> int:
        """清除用户所有警告"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM warnings 
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"清除了用户 {user_id} 在群组 {chat_id} 的 {deleted_count} 条警告")
        return deleted_count
    
    # ========== 群组设置相关方法 ==========
    
    def get_chat_setting(self, chat_id: int, setting_name: str, default_value=None):
        """获取群组设置"""
        # 白名单验证，防止 SQL 注入
        ALLOWED_SETTINGS = ['welcome_message', 'rules', 'auto_delete_ads', 
                           'welcome_new_members', 'auto_kick_bots', 
                           'created_at', 'updated_at']
        if setting_name not in ALLOWED_SETTINGS:
            raise ValueError(f"Invalid setting name: {setting_name}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT {setting_name} FROM chat_settings 
            WHERE chat_id = ?
        """, (chat_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] is not None:
            return result[0]
        return default_value
    
    def set_chat_setting(self, chat_id: int, setting_name: str, value):
        """设置群组设置"""
        # 白名单验证，防止 SQL 注入
        ALLOWED_SETTINGS = ['welcome_message', 'rules', 'auto_delete_ads', 
                           'welcome_new_members', 'auto_kick_bots']
        if setting_name not in ALLOWED_SETTINGS:
            raise ValueError(f"Invalid setting name: {setting_name}")
        
        import time
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查群组是否存在
        cursor.execute("""
            SELECT chat_id FROM chat_settings WHERE chat_id = ?
        """, (chat_id,))
        
        exists = cursor.fetchone()
        
        if exists:
            # 更新
            cursor.execute(f"""
                UPDATE chat_settings 
                SET {setting_name} = ?, updated_at = ?
                WHERE chat_id = ?
            """, (value, int(time.time()), chat_id))
        else:
            # 创建
            cursor.execute(f"""
                INSERT INTO chat_settings (chat_id, {setting_name}, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (chat_id, value, int(time.time()), int(time.time())))
        
        conn.commit()
        conn.close()
        logger.info(f"设置群组 {chat_id} 的 {setting_name} = {value}")
    
    def get_welcome_message(self, chat_id: int):
        """获取欢迎消息"""
        return self.get_chat_setting(chat_id, 'welcome_message', None)
    
    def set_welcome_message(self, chat_id: int, message: str):
        """设置欢迎消息"""
        self.set_chat_setting(chat_id, 'welcome_message', message)
    
    def get_rules(self, chat_id: int):
        """获取群规"""
        return self.get_chat_setting(chat_id, 'rules', None)
    
    def set_rules(self, chat_id: int, rules: str):
        """设置群规"""
        self.set_chat_setting(chat_id, 'rules', rules)
    
    def is_auto_delete_ads_enabled(self, chat_id: int) -> bool:
        """检查是否启用自动删除广告"""
        return bool(self.get_chat_setting(chat_id, 'auto_delete_ads', 1))
    
    def set_auto_delete_ads(self, chat_id: int, enabled: bool):
        """设置自动删除广告"""
        self.set_chat_setting(chat_id, 'auto_delete_ads', 1 if enabled else 0)
    
    def is_welcome_enabled(self, chat_id: int) -> bool:
        """检查是否启用欢迎消息"""
        return bool(self.get_chat_setting(chat_id, 'welcome_new_members', 1))
    
    def set_welcome_enabled(self, chat_id: int, enabled: bool):
        """设置是否启用欢迎消息"""
        self.set_chat_setting(chat_id, 'welcome_new_members', 1 if enabled else 0)


# 全局数据库实例
db = Database()


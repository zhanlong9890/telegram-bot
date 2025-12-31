"""
配置文件
集中管理所有配置选项，支持环境变量和默认值
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_env_int(key: str, default: int) -> int:
    """从环境变量获取整数，失败返回默认值"""
    try:
        return int(os.getenv(key, default))
    except (ValueError, TypeError):
        return default


def get_env_bool(key: str, default: bool) -> bool:
    """从环境变量获取布尔值，失败返回默认值"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


# ========== Bot 配置 ==========
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError(
        "❌ BOT_TOKEN 环境变量未设置！\n"
        "请在 .env 文件或环境变量中设置 BOT_TOKEN。\n"
        "示例: BOT_TOKEN=你的机器人Token"
    )

# 管理员ID列表（用逗号分隔）
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',') if admin_id.strip()]

# ========== 警告系统配置 ==========
MAX_WARN_LIMIT = get_env_int('MAX_WARN_LIMIT', 3)  # 最大警告次数，超过后自动踢出

# ========== 禁言配置 ==========
DEFAULT_BAN_TIME = get_env_int('DEFAULT_BAN_TIME', 86400)  # 默认禁言时间（秒），24小时
MAX_MUTE_TIME = get_env_int('MAX_MUTE_TIME', 2592000)  # 最大禁言时间（秒），30天

# ========== 积分系统配置 ==========
POINTS_PER_MESSAGE = get_env_int('POINTS_PER_MESSAGE', 1)  # 每条消息获得的积分
POINTS_COOLDOWN = get_env_int('POINTS_COOLDOWN', 60)  # 积分冷却时间（秒）
NEW_MEMBER_BONUS = get_env_int('NEW_MEMBER_BONUS', 10)  # 新成员奖励积分
AD_POINTS_PENALTY = get_env_int('AD_POINTS_PENALTY', 10)  # 发送广告扣除的积分
FLOOD_POINTS_PENALTY = get_env_int('FLOOD_POINTS_PENALTY', 5)  # 刷屏扣除的积分
DUPLICATE_POINTS_PENALTY = get_env_int('DUPLICATE_POINTS_PENALTY', 2)  # 重复消息扣除的积分

# ========== 防刷屏配置 ==========
FLOOD_LIMIT = get_env_int('FLOOD_LIMIT', 5)  # 刷屏限制（条数）
FLOOD_WINDOW = get_env_int('FLOOD_WINDOW', 10)  # 刷屏时间窗口（秒）
DUPLICATE_CHECK_COUNT = get_env_int('DUPLICATE_CHECK_COUNT', 5)  # 检测重复消息的历史记录数

# ========== 自动管理配置 ==========
AUTO_DELETE_ADS = get_env_bool('AUTO_DELETE_ADS', True)  # 默认启用自动删除广告
AUTO_WELCOME = get_env_bool('AUTO_WELCOME', True)  # 默认启用欢迎消息
AUTO_KICK_BOTS = get_env_bool('AUTO_KICK_BOTS', False)  # 默认不自动踢出机器人

# ========== 数据库配置 ==========
DB_PATH = os.getenv('DB_PATH', 'bot_data.db')  # 数据库文件路径
DB_BACKUP_ENABLED = get_env_bool('DB_BACKUP_ENABLED', True)  # 是否启用数据库备份
DB_BACKUP_INTERVAL = get_env_int('DB_BACKUP_INTERVAL', 86400)  # 备份间隔（秒），默认24小时

# ========== 日志配置 ==========
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_FILE = os.getenv('LOG_FILE', 'bot.log')  # 日志文件路径，空字符串表示不保存到文件

# ========== 性能配置 ==========
ADMIN_CACHE_TIMEOUT = get_env_int('ADMIN_CACHE_TIMEOUT', 300)  # 管理员权限缓存时间（秒）
MESSAGE_HANDLER_TIMEOUT = get_env_int('MESSAGE_HANDLER_TIMEOUT', 5)  # 消息处理器超时时间（秒）

# ========== 功能开关 ==========
ENABLE_POINTS_SYSTEM = get_env_bool('ENABLE_POINTS_SYSTEM', True)  # 是否启用积分系统
ENABLE_ANTI_SPAM = get_env_bool('ENABLE_ANTI_SPAM', True)  # 是否启用反垃圾功能
ENABLE_STATISTICS = get_env_bool('ENABLE_STATISTICS', True)  # 是否启用统计功能

# ========== 高级配置 ==========
MAX_MESSAGE_LENGTH = get_env_int('MAX_MESSAGE_LENGTH', 4096)  # 最大消息长度
RATE_LIMIT_ENABLED = get_env_bool('RATE_LIMIT_ENABLED', True)  # 是否启用速率限制
RATE_LIMIT_PER_USER = get_env_int('RATE_LIMIT_PER_USER', 20)  # 每个用户每分钟最大消息数


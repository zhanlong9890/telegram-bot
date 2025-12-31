"""
统计功能模块
提供群组统计、用户统计等功能
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
import logging
from database import db

logger = logging.getLogger(__name__)


async def check_admin_permission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """检查用户是否有管理员权限"""
    user = update.effective_user
    chat = update.effective_chat
    
    if not chat or chat.type == 'private':
        return False
    
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        logger.error(f"检查管理员权限时出错: {e}")
        return False


async def group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看群组/频道统计"""
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组或频道中使用！")
        return
    
    try:
        # 获取群组/频道信息
        chat_info = await context.bot.get_chat(chat.id)
        member_count = chat_info.members_count or 0
        
        chat_type_name = "频道" if chat.type == 'channel' else "群组"
        
        if chat.type == 'channel':
            # 频道统计（简化版，频道不支持积分和警告）
            stats_text = f"""
📊 频道统计

📺 频道名称: {chat.title or '未知'}
👥 订阅者: {member_count}
📌 类型: {'公开频道' if chat.username else '私有频道'}
            """
            
            if chat.username:
                stats_text += f"\n🔗 频道链接: https://t.me/{chat.username}"
        else:
            # 群组统计（完整版）
            # 获取积分统计
            top_users = db.get_top_users(chat.id, limit=1)
            total_users_with_points = len(db.get_top_users(chat.id, limit=1000))
            
            # 获取警告统计
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) FROM warnings WHERE chat_id = ?
            """, (chat.id,))
            warned_users = cursor.fetchone()[0] or 0
            conn.close()
            
            stats_text = f"""
📊 群组统计

👥 群组成员: {member_count}
💰 有积分用户: {total_users_with_points}
⚠️ 被警告用户: {warned_users}
📝 群组名称: {chat.title or '未知'}

💡 使用 /top 查看积分排行榜
            """
        
        await update.message.reply_text(stats_text)
        logger.info(f"用户 {update.effective_user.id} 查看了{chat_type_name} {chat.id} 的统计")
    except Exception as e:
        await update.message.reply_text(f"❌ 获取统计失败: {str(e)}")
        logger.error(f"获取{chat.type}统计时出错: {e}")


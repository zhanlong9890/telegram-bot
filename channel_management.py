"""
频道管理模块
专门处理频道（Channel）的管理功能
频道和群组的区别：
- 频道是单向的，管理员发布消息，用户只能接收
- 频道不支持踢人、禁言等群组功能
- 频道支持删除消息、统计等功能
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging
from database import db
from utils_common import check_admin_permission, require_admin, require_channel_or_group
from error_handler import safe_execute

logger = logging.getLogger(__name__)


@safe_execute
@require_admin
@require_channel_or_group
async def delete_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """删除频道消息（管理员）"""
    message = update.message
    chat = update.effective_chat
    
    # 检查是否回复了消息
    if not message.reply_to_message:
        await message.reply_text("⚠️ 请回复要删除的消息！\n用法: /del (回复消息)")
        return
    
    try:
        # 删除回复的消息
        await message.reply_to_message.delete()
        # 删除命令消息
        await message.delete()
        logger.info(f"频道管理员 {update.effective_user.id} 在频道 {chat.id} 删除了消息")
    except Exception as e:
        await message.reply_text(f"❌ 删除消息失败: {str(e)}")
        logger.error(f"删除频道消息时出错: {e}")


@safe_execute
@require_admin
@require_channel_or_group
async def channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看频道信息"""
    chat = update.effective_chat
    
    try:
        chat_info = await context.bot.get_chat(chat.id)
        
        info_text = f"""
📺 频道信息

📝 频道名称: {chat.title or '未知'}
🆔 频道ID: <code>{chat.id}</code>
👥 订阅者: {chat_info.members_count or '未知'}
📌 类型: {'频道' if chat.type == 'channel' else '群组'}
        """
        
        if chat_info.description:
            info_text += f"\n📄 频道描述:\n{chat_info.description}"
        
        if chat.username:
            info_text += f"\n🔗 频道链接: @{chat.username}"
        
        await update.message.reply_text(info_text, parse_mode='HTML')
        logger.info(f"用户 {update.effective_user.id} 查看了频道 {chat.id} 的信息")
    except Exception as e:
        await update.message.reply_text(f"❌ 获取频道信息失败: {str(e)}")
        logger.error(f"获取频道信息时出错: {e}")


@safe_execute
@require_admin
@require_channel_or_group
async def channel_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看频道管理员列表"""
    chat = update.effective_chat
    
    try:
        administrators = await context.bot.get_chat_administrators(chat.id)
        
        if not administrators:
            await update.message.reply_text("ℹ️ 此频道没有管理员")
            return
        
        admins_text = "👑 频道管理员列表\n\n"
        
        for admin in administrators:
            user = admin.user
            status = "频道主" if admin.status == "creator" else "管理员"
            
            if user.username:
                admins_text += f"• {status}: @{user.username}\n"
            else:
                admins_text += f"• {status}: {user.first_name} (ID: {user.id})\n"
        
        await update.message.reply_text(admins_text)
        logger.info(f"用户 {update.effective_user.id} 查看了频道 {chat.id} 的管理员列表")
    except Exception as e:
        await update.message.reply_text(f"❌ 获取管理员列表失败: {str(e)}")
        logger.error(f"获取频道管理员列表时出错: {e}")


@safe_execute
@require_admin
@require_channel_or_group
async def channel_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看频道统计"""
    chat = update.effective_chat
    
    try:
        chat_info = await context.bot.get_chat(chat.id)
        member_count = chat_info.members_count or 0
        
        stats_text = f"""
📊 频道统计

📺 频道名称: {chat.title or '未知'}
👥 订阅者数量: {member_count}
📌 频道类型: {'公开频道' if chat.username else '私有频道'}
        """
        
        if chat.username:
            stats_text += f"\n🔗 频道链接: https://t.me/{chat.username}"
        
        await update.message.reply_text(stats_text)
        logger.info(f"用户 {update.effective_user.id} 查看了频道 {chat.id} 的统计")
    except Exception as e:
        await update.message.reply_text(f"❌ 获取统计失败: {str(e)}")
        logger.error(f"获取频道统计时出错: {e}")


@safe_execute
@require_admin
@require_channel_or_group
async def pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """置顶消息（频道/群组）"""
    message = update.message
    chat = update.effective_chat
    
    # 检查是否回复了消息
    if not message.reply_to_message:
        await message.reply_text("⚠️ 请回复要置顶的消息！\n用法: /pin (回复消息)")
        return
    
    try:
        # 置顶消息
        await context.bot.pin_chat_message(
            chat.id,
            message.reply_to_message.message_id,
            disable_notification=False
        )
        await message.reply_text("✅ 消息已置顶")
        logger.info(f"管理员 {update.effective_user.id} 在 {chat.type} {chat.id} 置顶了消息")
    except Exception as e:
        await message.reply_text(f"❌ 置顶消息失败: {str(e)}")
        logger.error(f"置顶消息时出错: {e}")


@safe_execute
@require_admin
@require_channel_or_group
async def unpin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """取消置顶消息（频道/群组）"""
    message = update.message
    chat = update.effective_chat
    
    try:
        # 取消置顶所有消息
        await context.bot.unpin_all_chat_messages(chat.id)
        await message.reply_text("✅ 已取消所有置顶消息")
        logger.info(f"管理员 {update.effective_user.id} 在 {chat.type} {chat.id} 取消了置顶")
    except Exception as e:
        await message.reply_text(f"❌ 取消置顶失败: {str(e)}")
        logger.error(f"取消置顶时出错: {e}")


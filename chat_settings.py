"""
群组设置模块
管理群组的欢迎消息、规则等设置
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


async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """设置欢迎消息"""
    if not await check_admin_permission(update, context):
        await update.message.reply_text("❌ 您没有权限使用此命令！")
        return
    
    message = update.message
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持欢迎消息功能！\n此功能仅在群组中可用。")
        return
    
    # 获取欢迎消息内容
    if not context.args:
        await message.reply_text(
            "⚠️ 用法错误！\n"
            "用法: /setwelcome <欢迎消息>\n"
            "示例: /setwelcome 欢迎 {username} 加入！\n\n"
            "可用占位符:\n"
            "{username} - 用户名\n"
            "{first_name} - 名字\n"
            "{chat_title} - 群组名称"
        )
        return
    
    welcome_text = " ".join(context.args)
    
    try:
        db.set_welcome_message(chat.id, welcome_text)
        await message.reply_text(
            f"✅ 欢迎消息已设置！\n\n预览:\n{welcome_text.replace('{username}', '新成员').replace('{first_name}', '新成员').replace('{chat_title}', chat.title or '本群')}"
        )
        logger.info(f"管理员 {update.effective_user.id} 设置了群组 {chat.id} 的欢迎消息")
    except Exception as e:
        await message.reply_text(f"❌ 设置失败: {str(e)}")
        logger.error(f"设置欢迎消息时出错: {e}")


async def get_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看欢迎消息"""
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持欢迎消息功能！\n此功能仅在群组中可用。")
        return
    
    welcome_text = db.get_welcome_message(chat.id)
    
    if welcome_text:
        await update.message.reply_text(
            f"📝 当前欢迎消息:\n\n{welcome_text}\n\n"
            f"可用占位符: {{username}}, {{first_name}}, {{chat_title}}"
        )
    else:
        await update.message.reply_text("ℹ️ 当前使用默认欢迎消息\n使用 /setwelcome 设置自定义欢迎消息")


async def set_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """设置群规"""
    if not await check_admin_permission(update, context):
        await update.message.reply_text("❌ 您没有权限使用此命令！")
        return
    
    message = update.message
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持群规功能！\n此功能仅在群组中可用。")
        return
    
    # 获取群规内容
    if not context.args:
        await message.reply_text(
            "⚠️ 用法错误！\n"
            "用法: /setrules <群规内容>\n"
            "示例: /setrules 1. 禁止广告\n2. 禁止刷屏"
        )
        return
    
    rules_text = " ".join(context.args)
    
    try:
        db.set_rules(chat.id, rules_text)
        await message.reply_text(f"✅ 群规已设置！\n\n{rules_text}")
        logger.info(f"管理员 {update.effective_user.id} 设置了群组 {chat.id} 的群规")
    except Exception as e:
        await message.reply_text(f"❌ 设置失败: {str(e)}")
        logger.error(f"设置群规时出错: {e}")


async def get_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看群规（频道也支持查看，但不支持设置）"""
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组或频道中使用！")
        return
    
    # 频道可以查看规则（如果有的话），但不能设置
    if chat.type == 'channel':
        rules_text = db.get_rules(chat.id)
        if rules_text:
            await update.message.reply_text(f"📋 频道规则:\n\n{rules_text}")
        else:
            await update.message.reply_text("ℹ️ 当前没有设置规则\n注意：频道不支持设置规则功能")
        return
    
    rules_text = db.get_rules(chat.id)
    
    if rules_text:
        await update.message.reply_text(f"📋 群规:\n\n{rules_text}")
    else:
        await update.message.reply_text("ℹ️ 当前没有设置群规\n使用 /setrules 设置群规")


async def toggle_auto_delete_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """切换自动删除广告功能"""
    if not await check_admin_permission(update, context):
        await update.message.reply_text("❌ 您没有权限使用此命令！")
        return
    
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持自动删除广告功能！\n此功能仅在群组中可用。")
        return
    
    current_status = db.is_auto_delete_ads_enabled(chat.id)
    new_status = not current_status
    
    try:
        db.set_auto_delete_ads(chat.id, new_status)
        status_text = "已启用" if new_status else "已禁用"
        await update.message.reply_text(f"✅ 自动删除广告功能 {status_text}")
        logger.info(f"管理员 {update.effective_user.id} {'启用' if new_status else '禁用'}了群组 {chat.id} 的自动删除广告功能")
    except Exception as e:
        await update.message.reply_text(f"❌ 操作失败: {str(e)}")
        logger.error(f"切换自动删除广告功能时出错: {e}")


async def toggle_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """切换欢迎消息功能"""
    if not await check_admin_permission(update, context):
        await update.message.reply_text("❌ 您没有权限使用此命令！")
        return
    
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持欢迎消息功能！\n此功能仅在群组中可用。")
        return
    
    current_status = db.is_welcome_enabled(chat.id)
    new_status = not current_status
    
    try:
        db.set_welcome_enabled(chat.id, new_status)
        status_text = "已启用" if new_status else "已禁用"
        await update.message.reply_text(f"✅ 欢迎消息功能 {status_text}")
        logger.info(f"管理员 {update.effective_user.id} {'启用' if new_status else '禁用'}了群组 {chat.id} 的欢迎消息功能")
    except Exception as e:
        await update.message.reply_text(f"❌ 操作失败: {str(e)}")
        logger.error(f"切换欢迎消息功能时出错: {e}")


async def chat_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看群组设置"""
    if not await check_admin_permission(update, context):
        await update.message.reply_text("❌ 您没有权限使用此命令！")
        return
    
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持群组设置功能！\n频道仅支持删除消息、置顶等基础功能。")
        return
    
    auto_delete = "✅ 启用" if db.is_auto_delete_ads_enabled(chat.id) else "❌ 禁用"
    welcome = "✅ 启用" if db.is_welcome_enabled(chat.id) else "❌ 禁用"
    welcome_msg = db.get_welcome_message(chat.id) or "默认消息"
    rules = db.get_rules(chat.id) or "未设置"
    
    settings_text = f"""
⚙️ 群组设置

🛡️ 自动删除广告: {auto_delete}
👋 欢迎新成员: {welcome}
📝 欢迎消息: {welcome_msg[:50]}{'...' if len(welcome_msg) > 50 else ''}
📋 群规: {rules[:50]}{'...' if len(rules) > 50 else ''}

💡 使用 /help 查看所有设置命令
    """
    
    await update.message.reply_text(settings_text)


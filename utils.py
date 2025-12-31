"""
实用工具模块
包含获取ID、群组信息等实用功能
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """获取用户ID和群组ID"""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        # 私聊模式
        text = f"""
🆔 你的信息

👤 用户ID: <code>{user.id}</code>
👤 用户名: @{user.username or '无'}
📛 昵称: {user.first_name} {user.last_name or ''}
        """
    else:
        # 群组模式
        text = f"""
🆔 ID 信息

👤 你的用户ID: <code>{user.id}</code>
💬 群组ID: <code>{chat.id}</code>
👤 用户名: @{user.username or '无'}
📛 昵称: {user.first_name} {user.last_name or ''}
📝 群组名称: {chat.title or '未知'}
        """
    
    await update.message.reply_text(text, parse_mode='HTML')


async def group_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看群组/频道详细信息"""
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组或频道中使用！")
        return
    
    try:
        chat_info = await context.bot.get_chat(chat.id)
        
        chat_type_name = "频道" if chat.type == 'channel' else "群组"
        
        info_text = f"""
📋 {chat_type_name}信息

📝 {chat_type_name}名称: {chat.title or '未知'}
🆔 {chat_type_name}ID: <code>{chat.id}</code>
👥 {'订阅者' if chat.type == 'channel' else '成员'}数量: {chat_info.members_count or '未知'}
📌 类型: {chat.type}
        """
        
        if chat_info.description:
            info_text += f"\n📄 {chat_type_name}描述:\n{chat_info.description}"
        
        if chat.username:
            info_text += f"\n🔗 {'频道' if chat.type == 'channel' else '群组'}链接: @{chat.username}"
        
        await update.message.reply_text(info_text, parse_mode='HTML')
        logger.info(f"用户 {update.effective_user.id} 查看了{chat_type_name} {chat.id} 的信息")
    except Exception as e:
        await update.message.reply_text(f"❌ 获取信息失败: {str(e)}")
        logger.error(f"获取{chat.type}信息时出错: {e}")


async def admins_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看管理员列表（群组/频道）"""
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组或频道中使用！")
        return
    
    try:
        administrators = await context.bot.get_chat_administrators(chat.id)
        
        chat_type_name = "频道" if chat.type == 'channel' else "群组"
        
        if not administrators:
            await update.message.reply_text(f"ℹ️ 此{chat_type_name}没有管理员")
            return
        
        admins_text = f"👑 {chat_type_name}管理员列表\n\n"
        
        for admin in administrators:
            user = admin.user
            chat_type_name = "频道" if chat.type == 'channel' else "群组"
            status = f"{chat_type_name}主" if admin.status == "creator" else "管理员"
            
            if user.username:
                admins_text += f"• {status}: @{user.username}\n"
            else:
                admins_text += f"• {status}: {user.first_name} (ID: {user.id})\n"
        
        await update.message.reply_text(admins_text)
        logger.info(f"用户 {update.effective_user.id} 查看了群组 {chat.id} 的管理员列表")
    except Exception as e:
        await update.message.reply_text(f"❌ 获取管理员列表失败: {str(e)}")
        logger.error(f"获取管理员列表时出错: {e}")


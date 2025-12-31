"""
Telegram 群管机器人
支持踢人、禁言、警告等群组管理功能
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, MAX_WARN_LIMIT, LOG_LEVEL, LOG_FILE
from admin_commands import (
    ban_user, unban_user, mute_user, unmute_user,
    warn_user, delete_message, get_user_info, unwarn_user, get_warnings
)
from points_system import (
    my_points, points_leaderboard, add_points_command,
    remove_points_command, set_points_command,
    handle_message_points
)
from auto_moderation import (
    auto_delete_ads, welcome_new_member
)
from chat_settings import (
    set_welcome, get_welcome, set_rules, get_rules,
    toggle_auto_delete_ads, toggle_welcome, chat_settings
)
from anti_spam import (
    anti_flood, detect_duplicate_messages
)
from statistics import group_stats
from utils import get_id, group_info, admins_list
from channel_management import (
    delete_channel_message, channel_info, channel_admins,
    channel_stats, pin_message, unpin_message
)

# 配置日志
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
log_handlers = [logging.StreamHandler()]

# 如果配置了日志文件，添加文件处理器
if LOG_FILE:
    log_handlers.append(logging.FileHandler(LOG_FILE, encoding='utf-8'))

logging.basicConfig(
    format=log_format,
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    handlers=log_handlers
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令（根据聊天类型显示不同内容）"""
    chat = update.effective_chat
    
    if chat and chat.type == 'channel':
        # 频道专用帮助
        welcome_text = """
🤖 欢迎使用频道管理机器人！

📺 频道管理员可用命令：

🔧 基础管理：
/del - 删除消息（回复消息）
/pin - 置顶消息（回复消息）
/unpin - 取消所有置顶消息

📊 信息查看：
/id - 获取频道ID
/groupinfo - 查看频道信息
/admins - 查看管理员列表
/stats - 查看频道统计

/help - 显示详细帮助

⚠️ 注意：频道不支持踢人、禁言、积分等功能
        """
    else:
        # 群组/私聊帮助
        welcome_text = """
🤖 欢迎使用群管机器人！

📋 管理命令（仅管理员）：
/ban - 踢出用户
/unban - 解封用户
/mute [时间] - 禁言用户
/unmute - 解除禁言
/warn [原因] - 警告用户
/unwarn - 清除警告
/warns - 查看警告次数
/del - 删除消息
/info - 查看用户信息

💰 积分命令：
/points - 查看自己的积分
/top - 查看积分排行榜

📊 实用工具：
/id - 获取用户ID和群组ID
/groupinfo - 查看群组信息
/admins - 查看管理员列表
/stats - 查看统计（管理员）
/pin - 置顶消息（管理员）
/unpin - 取消置顶（管理员）

⚙️ 群组设置（仅管理员）：
/setwelcome <消息> - 设置欢迎消息
/getwelcome - 查看欢迎消息
/setrules <规则> - 设置群规
/rules - 查看群规
/settings - 查看群组设置

/help - 显示详细帮助
        """
    
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令（根据聊天类型显示不同内容）"""
    chat = update.effective_chat
    
    if chat and chat.type == 'channel':
        # 频道专用帮助
        help_text = """
📖 频道管理员命令说明：

🔧 基础管理：
• /del - 删除消息（回复消息）
• /pin - 置顶消息（回复消息）
• /unpin - 取消所有置顶消息

📊 信息查看：
• /id - 获取频道ID
• /groupinfo - 查看频道信息
• /admins - 查看管理员列表
• /stats - 查看频道统计

⚠️ 频道不支持的功能：
• ❌ 踢人、禁言、警告（频道没有成员概念）
• ❌ 积分系统（频道是单向的）
• ❌ 自动管理功能（不适用）
• ❌ 群组设置（不适用）

💡 频道特点：
• 频道是单向广播，管理员发布消息
• 用户只能接收消息，不能互动
• 适合新闻发布、公告通知等场景
        """
    else:
        # 群组/私聊帮助
        help_text = """
📖 群组命令说明：

🔨 管理命令（仅管理员）：
• /ban - 踢出用户（回复用户消息）
• /unban - 解封用户（回复用户消息）
• /mute [时间] - 禁言用户（回复用户消息，时间单位：秒）
• /unmute - 解除禁言（回复用户消息）
• /warn [原因] - 警告用户（回复用户消息）
• /unwarn - 清除用户所有警告（回复用户消息）
• /warns - 查看用户警告次数（回复用户消息）
• /del - 删除消息（回复消息）
• /info - 查看用户信息（回复用户消息）

💰 积分命令：
• /points - 查看自己的积分
• /top - 查看积分排行榜（前10名）
• /points [用户] - 查看指定用户积分（管理员，回复用户消息）

🔧 积分管理（仅管理员）：
• /addpoints <数量> [原因] - 给用户添加积分（回复用户消息）
• /removepoints <数量> [原因] - 扣除用户积分（回复用户消息）
• /setpoints <数量> - 设置用户积分（回复用户消息）

💡 积分规则：
• 在群组中发言可以获得积分（每条消息1分）
• 60秒内只能获得一次积分（防刷分）
• 积分可以用于排名和奖励

⚙️ 群组设置（仅管理员）：
• /setwelcome <消息> - 设置欢迎消息（支持占位符：{username}, {first_name}, {chat_title}）
• /getwelcome - 查看当前欢迎消息
• /setrules <规则> - 设置群规
• /rules - 查看群规
• /settings - 查看所有群组设置

🤖 自动功能：
• 自动删除广告（可开关）
• 自动欢迎新成员（可开关）
• 防刷屏（10秒内超过5条消息自动删除）
• 检测重复消息（自动删除）
• 新成员加入奖励10积分

📊 实用工具：
• /id - 获取用户ID和群组ID
• /groupinfo - 查看群组详细信息
• /admins - 查看管理员列表
• /stats - 查看统计（管理员）
• /pin - 置顶消息（管理员）
• /unpin - 取消置顶（管理员）

⚠️ 权限说明：
• 管理命令和设置命令只有群组管理员和群主可以使用
• 普通用户可以使用 /points、/top、/rules 查看信息
        """
    
    await update.message.reply_text(help_text)


# 导入新的错误处理器
from error_handler import error_handler


def main():
    """主函数"""
    # 创建应用
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 注册命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # 管理命令（群组专用，已用 @require_group 装饰器限制）
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("unwarn", unwarn_user))
    application.add_handler(CommandHandler("warns", get_warnings))
    
    # 通用管理命令（群组/频道都支持）
    application.add_handler(CommandHandler("del", delete_message))
    application.add_handler(CommandHandler("info", get_user_info))
    
    # 积分命令
    application.add_handler(CommandHandler("points", my_points))
    application.add_handler(CommandHandler("top", points_leaderboard))
    application.add_handler(CommandHandler("addpoints", add_points_command))
    application.add_handler(CommandHandler("removepoints", remove_points_command))
    application.add_handler(CommandHandler("setpoints", set_points_command))
    
    # 群组设置命令
    application.add_handler(CommandHandler("setwelcome", set_welcome))
    application.add_handler(CommandHandler("getwelcome", get_welcome))
    application.add_handler(CommandHandler("setrules", set_rules))
    application.add_handler(CommandHandler("rules", get_rules))
    application.add_handler(CommandHandler("settings", chat_settings))
    application.add_handler(CommandHandler("toggleads", toggle_auto_delete_ads))
    application.add_handler(CommandHandler("togglewelcome", toggle_welcome))
    
    # 实用工具命令
    application.add_handler(CommandHandler("id", get_id))
    application.add_handler(CommandHandler("chatid", get_id))  # 别名
    application.add_handler(CommandHandler("groupinfo", group_info))
    application.add_handler(CommandHandler("admins", admins_list))
    application.add_handler(CommandHandler("stats", group_stats))
    
    # 频道管理命令（也支持群组）
    application.add_handler(CommandHandler("pin", pin_message))
    application.add_handler(CommandHandler("unpin", unpin_message))
    
    # 消息处理器（仅群组，频道中不执行）
    # 注意：这些功能在频道中会被自动跳过（函数内部检查）
    # 1. 先处理反垃圾（防刷屏、重复消息）
    # 2. 再处理广告检测
    # 3. 最后处理积分奖励
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        anti_flood,
        block=False
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        detect_duplicate_messages,
        block=False
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        auto_delete_ads,
        block=False
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message_points
    ))
    
    # 新成员加入处理器（仅群组）
    application.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS,
        welcome_new_member
    ))
    
    # 注册错误处理器
    application.add_error_handler(error_handler)
    
    # 启动机器人
    logger.info("机器人启动中...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()


"""
积分系统模块
处理积分相关的命令和自动积分奖励
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging
from database import db
from config import POINTS_PER_MESSAGE, POINTS_COOLDOWN, NEW_MEMBER_BONUS
from utils_common import check_admin_permission, require_admin, require_group
from error_handler import safe_execute

logger = logging.getLogger(__name__)


async def handle_message_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理消息积分奖励（自动调用）"""
    if not update.message or not update.effective_chat:
        return
    
    chat = update.effective_chat
    user = update.effective_user
    
    # 只处理群组消息（不包括频道和私聊）
    if chat.type == 'private' or chat.type == 'channel':
        return
    
    # 忽略机器人消息
    if user.is_bot:
        return
    
    # 检查冷却时间（防止刷分）
    if not db.can_earn_points(chat.id, user.id, cooldown=POINTS_COOLDOWN):
        return
    
    # 奖励积分
    new_points = db.add_points(chat.id, user.id, POINTS_PER_MESSAGE, "发送消息")
    
    # 更新最后发言时间
    db.update_last_message_time(chat.id, user.id)
    
    # 记录日志（不发送消息，避免刷屏）
    logger.debug(f"用户 {user.id} 在群组 {chat.id} 获得 {POINTS_PER_MESSAGE} 积分，当前积分: {new_points}")


async def my_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看自己的积分或指定用户的积分"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持积分功能！\n积分功能仅在群组中可用。")
        return
    
    # 如果回复了消息，查看被回复用户的积分（需要管理员权限）
    if update.message.reply_to_message:
        if await check_admin_permission(update, context):
            target_user = update.message.reply_to_message.from_user
            points = db.get_user_points(chat.id, target_user.id)
            rank = db.get_user_rank(chat.id, target_user.id)
            
            rank_text = f"🏆 排名: 第 {rank} 名" if rank else "📊 排名: 暂无排名"
            
            text = f"""
👤 用户积分信息

👤 用户: {target_user.mention_html()}
💎 积分: <b>{points}</b>
{rank_text}
            """
            
            await update.message.reply_text(text, parse_mode='HTML')
            return
        else:
            await update.message.reply_text("❌ 您没有权限查看其他用户的积分！")
            return
    
    # 查看自己的积分
    points = db.get_user_points(chat.id, user.id)
    rank = db.get_user_rank(chat.id, user.id)
    
    rank_text = f"🏆 排名: 第 {rank} 名" if rank else "📊 排名: 暂无排名"
    
    text = f"""
💰 你的积分信息

💎 当前积分: <b>{points}</b>
{rank_text}

💡 提示: 在群组中发言可以获得积分！
    """
    
    await update.message.reply_text(text, parse_mode='HTML')


async def points_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看积分排行榜"""
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持积分功能！\n积分功能仅在群组中可用。")
        return
    
    # 获取前10名
    top_users = db.get_top_users(chat.id, limit=10)
    
    if not top_users:
        await update.message.reply_text("📊 排行榜为空，还没有人获得积分！")
        return
    
    text = "🏆 <b>积分排行榜</b>\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    
    for index, (user_id, points) in enumerate(top_users, 1):
        try:
            # 获取用户信息
            member = await context.bot.get_chat_member(chat.id, user_id)
            user = member.user
            
            # 显示用户名或昵称
            if user.username:
                name = f"@{user.username}"
            else:
                name = user.first_name or f"用户{user_id}"
            
            # 添加奖牌
            medal = medals[index - 1] if index <= 3 else f"{index}."
            
            text += f"{medal} {name}: <b>{points}</b> 分\n"
        except Exception as e:
            logger.error(f"获取用户 {user_id} 信息失败: {e}")
            text += f"{index}. 用户{user_id}: <b>{points}</b> 分\n"
    
    await update.message.reply_text(text, parse_mode='HTML')


async def add_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员给用户添加积分"""
    if not await check_admin_permission(update, context):
        await update.message.reply_text("❌ 您没有权限使用此命令！")
        return
    
    message = update.message
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持积分功能！\n积分功能仅在群组中可用。")
        return
    
    # 检查参数
    if not context.args or len(context.args) < 2:
        await message.reply_text(
            "⚠️ 用法错误！\n"
            "用法: /addpoints <积分> (回复用户消息)\n"
            "示例: /addpoints 100"
        )
        return
    
    # 检查是否回复了消息
    if not message.reply_to_message:
        await message.reply_text("⚠️ 请回复要添加积分的用户消息！")
        return
    
    try:
        points = int(context.args[0])
        if points <= 0:
            await message.reply_text("❌ 积分必须是正整数！")
            return
        
        target_user = message.reply_to_message.from_user
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "管理员奖励"
        
        new_points = db.add_points(chat.id, target_user.id, points, reason)
        
        await message.reply_text(
            f"✅ 已给 {target_user.mention_html()} 添加 <b>{points}</b> 积分\n"
            f"💎 当前积分: <b>{new_points}</b>",
            parse_mode='HTML'
        )
        logger.info(f"管理员 {update.effective_user.id} 给用户 {target_user.id} 添加了 {points} 积分")
    except ValueError:
        await message.reply_text("❌ 积分必须是数字！")
    except Exception as e:
        await message.reply_text(f"❌ 操作失败: {str(e)}")
        logger.error(f"添加积分时出错: {e}")


async def remove_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员扣除用户积分"""
    if not await check_admin_permission(update, context):
        await update.message.reply_text("❌ 您没有权限使用此命令！")
        return
    
    message = update.message
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持积分功能！\n积分功能仅在群组中可用。")
        return
    
    # 检查参数
    if not context.args or len(context.args) < 1:
        await message.reply_text(
            "⚠️ 用法错误！\n"
            "用法: /removepoints <积分> (回复用户消息)\n"
            "示例: /removepoints 50"
        )
        return
    
    # 检查是否回复了消息
    if not message.reply_to_message:
        await message.reply_text("⚠️ 请回复要扣除积分的用户消息！")
        return
    
    try:
        points = int(context.args[0])
        if points <= 0:
            await message.reply_text("❌ 积分必须是正整数！")
            return
        
        target_user = message.reply_to_message.from_user
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "管理员扣除"
        
        new_points = db.subtract_points(chat.id, target_user.id, points, reason)
        
        # 确保积分不为负
        if new_points < 0:
            db.set_points(chat.id, target_user.id, 0)
            new_points = 0
        
        await message.reply_text(
            f"✅ 已扣除 {target_user.mention_html()} <b>{points}</b> 积分\n"
            f"💎 当前积分: <b>{new_points}</b>",
            parse_mode='HTML'
        )
        logger.info(f"管理员 {update.effective_user.id} 扣除了用户 {target_user.id} {points} 积分")
    except ValueError:
        await message.reply_text("❌ 积分必须是数字！")
    except Exception as e:
        await message.reply_text(f"❌ 操作失败: {str(e)}")
        logger.error(f"扣除积分时出错: {e}")


async def set_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员设置用户积分（覆盖）"""
    if not await check_admin_permission(update, context):
        await update.message.reply_text("❌ 您没有权限使用此命令！")
        return
    
    message = update.message
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("❌ 此命令只能在群组中使用！")
        return
    
    if chat.type == 'channel':
        await update.message.reply_text("❌ 频道不支持积分功能！\n积分功能仅在群组中可用。")
        return
    
    # 检查参数
    if not context.args or len(context.args) < 1:
        await message.reply_text(
            "⚠️ 用法错误！\n"
            "用法: /setpoints <积分> (回复用户消息)\n"
            "示例: /setpoints 1000"
        )
        return
    
    # 检查是否回复了消息
    if not message.reply_to_message:
        await message.reply_text("⚠️ 请回复要设置积分的用户消息！")
        return
    
    try:
        points = int(context.args[0])
        if points < 0:
            await message.reply_text("❌ 积分不能为负数！")
            return
        
        target_user = message.reply_to_message.from_user
        new_points = db.set_points(chat.id, target_user.id, points)
        
        await message.reply_text(
            f"✅ 已将 {target_user.mention_html()} 的积分设置为 <b>{new_points}</b>",
            parse_mode='HTML'
        )
        logger.info(f"管理员 {update.effective_user.id} 将用户 {target_user.id} 的积分设置为 {new_points}")
    except ValueError:
        await message.reply_text("❌ 积分必须是数字！")
    except Exception as e:
        await message.reply_text(f"❌ 操作失败: {str(e)}")
        logger.error(f"设置积分时出错: {e}")




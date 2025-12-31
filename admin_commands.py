"""
群管功能模块
包含踢人、禁言、警告等管理功能
"""
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
import logging
from database import db
from config import MAX_WARN_LIMIT, DEFAULT_BAN_TIME, MAX_MUTE_TIME
from utils_common import check_admin_permission, require_admin, require_group, require_reply, require_channel_or_group, format_time
from error_handler import safe_execute

logger = logging.getLogger(__name__)


@safe_execute
@require_admin
@require_group
@require_reply
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """踢出用户"""
    chat = update.effective_chat
    message = update.message
    
    target_user = message.reply_to_message.from_user
    
    try:
        # 踢出用户
        await context.bot.ban_chat_member(chat.id, target_user.id)
        await message.reply_text(f"✅ 已踢出用户: {target_user.mention_html()}", parse_mode='HTML')
        logger.info(f"用户 {update.effective_user.id} 踢出了用户 {target_user.id}")
    except Exception as e:
        await message.reply_text(f"❌ 踢出用户失败: {str(e)}")
        logger.error(f"踢出用户时出错: {e}")


@safe_execute
@require_admin
@require_group
@require_reply
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """解封用户"""
    chat = update.effective_chat
    message = update.message
    
    target_user = message.reply_to_message.from_user
    
    try:
        # 解封用户
        await context.bot.unban_chat_member(chat.id, target_user.id, only_if_banned=True)
        await message.reply_text(f"✅ 已解封用户: {target_user.mention_html()}", parse_mode='HTML')
        logger.info(f"用户 {update.effective_user.id} 解封了用户 {target_user.id}")
    except Exception as e:
        await message.reply_text(f"❌ 解封用户失败: {str(e)}")
        logger.error(f"解封用户时出错: {e}")


@safe_execute
@require_admin
@require_group
@require_reply
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """禁言用户"""
    chat = update.effective_chat
    message = update.message
    
    target_user = message.reply_to_message.from_user
    
    # 解析禁言时间，默认24小时
    mute_time = 86400  # 默认24小时
    if context.args:
        try:
            mute_time = int(context.args[0])
        except ValueError:
            await message.reply_text("⚠️ 时间格式错误，使用默认24小时")
    
    try:
        # 禁言用户（禁止所有消息权限）
        from telegram import ChatPermissions
        
        mute_permissions = ChatPermissions(
            can_send_messages=False,
            can_send_audios=False,
            can_send_documents=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_video_notes=False,
            can_send_voice_notes=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        
        until_date = None if mute_time == 0 else (message.date.timestamp() + mute_time)
        await context.bot.restrict_chat_member(
            chat.id,
            target_user.id,
            until_date=until_date,
            permissions=mute_permissions
        )
        time_str = f"{mute_time // 3600}小时" if mute_time >= 3600 else f"{mute_time // 60}分钟"
        await message.reply_text(f"✅ 已禁言用户: {target_user.mention_html()} ({time_str})", parse_mode='HTML')
        logger.info(f"用户 {update.effective_user.id} 禁言了用户 {target_user.id} {time_str}")
    except Exception as e:
        await message.reply_text(f"❌ 禁言用户失败: {str(e)}")
        logger.error(f"禁言用户时出错: {e}")


@safe_execute
@require_admin
@require_group
@require_reply
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """解除禁言"""
    chat = update.effective_chat
    message = update.message
    
    target_user = message.reply_to_message.from_user
    
    try:
        # 恢复用户权限（允许所有权限）
        from telegram import ChatPermissions
        
        # 创建允许所有权限的权限对象
        full_permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        
        await context.bot.restrict_chat_member(
            chat.id,
            target_user.id,
            permissions=full_permissions
        )
        await message.reply_text(f"✅ 已解除禁言: {target_user.mention_html()}", parse_mode='HTML')
        logger.info(f"用户 {update.effective_user.id} 解除了用户 {target_user.id} 的禁言")
    except Exception as e:
        await message.reply_text(f"❌ 解除禁言失败: {str(e)}")
        logger.error(f"解除禁言时出错: {e}")


@safe_execute
@require_admin
@require_group
@require_reply
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """警告用户"""
    message = update.message
    chat = update.effective_chat
    
    target_user = message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "无"
    
    try:
        # 添加警告记录到数据库
        warning_count = db.add_warning(chat.id, target_user.id, update.effective_user.id, reason)
        
        warn_text = f"""
⚠️ 警告用户: {target_user.mention_html()}

📝 原因: {reason}
📊 警告次数: <b>{warning_count}/{MAX_WARN_LIMIT}</b>
        """
        
        await message.reply_text(warn_text, parse_mode='HTML')
        
        # 如果达到警告上限，自动踢出
        if warning_count >= MAX_WARN_LIMIT:
            try:
                await context.bot.ban_chat_member(chat.id, target_user.id)
                await message.reply_text(
                    f"🚫 用户 {target_user.mention_html()} 已达到警告上限，已自动踢出！",
                    parse_mode='HTML'
                )
                logger.info(f"用户 {target_user.id} 达到警告上限，已自动踢出")
            except Exception as e:
                logger.error(f"自动踢出用户失败: {e}")
        
        logger.info(f"用户 {update.effective_user.id} 警告了用户 {target_user.id}, 原因: {reason}, 当前警告: {warning_count}")
    except Exception as e:
        await message.reply_text(f"❌ 警告失败: {str(e)}")
        logger.error(f"警告用户时出错: {e}")


@safe_execute
@require_admin
@require_group
@require_reply
async def unwarn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """清除用户所有警告"""
    message = update.message
    chat = update.effective_chat
    
    target_user = message.reply_to_message.from_user
    
    try:
        deleted_count = db.clear_warnings(chat.id, target_user.id)
        
        if deleted_count > 0:
            await message.reply_text(
                f"✅ 已清除 {target_user.mention_html()} 的 <b>{deleted_count}</b> 条警告记录",
                parse_mode='HTML'
            )
        else:
            await message.reply_text(
                f"ℹ️ 用户 {target_user.mention_html()} 没有警告记录",
                parse_mode='HTML'
            )
        
        logger.info(f"管理员 {update.effective_user.id} 清除了用户 {target_user.id} 的 {deleted_count} 条警告")
    except Exception as e:
        await message.reply_text(f"❌ 清除警告失败: {str(e)}")
        logger.error(f"清除警告时出错: {e}")


@safe_execute
@require_admin
@require_group
@require_reply
async def get_warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看用户警告次数"""
    message = update.message
    chat = update.effective_chat
    
    target_user = message.reply_to_message.from_user
    
    try:
        warning_count = db.get_warning_count(chat.id, target_user.id)
        
        warn_text = f"""
📊 用户警告信息

👤 用户: {target_user.mention_html()}
⚠️ 警告次数: <b>{warning_count}/{MAX_WARN_LIMIT}</b>
        """
        
        if warning_count >= MAX_WARN_LIMIT:
            warn_text += "\n🚫 已达到警告上限！"
        elif warning_count > 0:
            remaining = MAX_WARN_LIMIT - warning_count
            warn_text += f"\n⚠️ 再警告 <b>{remaining}</b> 次将自动踢出"
        
        await message.reply_text(warn_text, parse_mode='HTML')
        logger.info(f"管理员 {update.effective_user.id} 查看了用户 {target_user.id} 的警告次数: {warning_count}")
    except Exception as e:
        await message.reply_text(f"❌ 查询失败: {str(e)}")
        logger.error(f"查询警告次数时出错: {e}")


async def delete_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """删除消息"""
    if not await check_admin_permission(update, context):
        await update.message.reply_text("❌ 您没有权限使用此命令！")
        return
    
    message = update.message
    
    # 检查是否回复了消息
    if not message.reply_to_message:
        await message.reply_text("⚠️ 请回复要删除的消息！\n用法: /del (回复消息)")
        return
    
    try:
        # 删除回复的消息
        await message.reply_to_message.delete()
        # 删除命令消息
        await message.delete()
        logger.info(f"用户 {update.effective_user.id} 删除了消息")
    except Exception as e:
        await message.reply_text(f"❌ 删除消息失败: {str(e)}")
        logger.error(f"删除消息时出错: {e}")


@safe_execute
@require_admin
@require_channel_or_group
@require_reply
async def get_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """获取用户信息（群组/频道都支持）"""
    message = update.message
    
    target_user = message.reply_to_message.from_user
    chat = update.effective_chat
    
    try:
        # 获取用户在群组中的信息
        member = await context.bot.get_chat_member(chat.id, target_user.id)
        
        info_text = f"""
👤 用户信息

🆔 ID: <code>{target_user.id}</code>
👤 用户名: @{target_user.username or '无'}
📛 昵称: {target_user.first_name} {target_user.last_name or ''}
📊 状态: {member.status}
🤖 是否机器人: {'是' if target_user.is_bot else '否'}
        """
        
        await message.reply_text(info_text, parse_mode='HTML')
        logger.info(f"用户 {update.effective_user.id} 查看了用户 {target_user.id} 的信息")
    except Exception as e:
        await message.reply_text(f"❌ 获取用户信息失败: {str(e)}")
        logger.error(f"获取用户信息时出错: {e}")


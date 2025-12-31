"""
反垃圾功能模块
包含防刷屏、检测重复消息等功能
"""
import time
import logging
from collections import defaultdict, deque
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
from database import db
from config import FLOOD_LIMIT, FLOOD_WINDOW, FLOOD_POINTS_PENALTY, DUPLICATE_POINTS_PENALTY
from utils_common import check_admin_permission
from error_handler import safe_execute

logger = logging.getLogger(__name__)

# 存储用户消息历史（用于检测刷屏和重复消息）
# 格式: {(chat_id, user_id): deque([timestamp1, timestamp2, ...])}
user_message_times = defaultdict(lambda: deque(maxlen=10))
user_message_texts = defaultdict(lambda: deque(maxlen=5))  # 存储最近5条消息文本


async def anti_flood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """防刷屏功能 - 限制消息频率"""
    if not update.message or not update.effective_chat:
        return
    
    chat = update.effective_chat
    message = update.message
    user = update.effective_user
    
    # 只处理群组消息（不包括频道和私聊）
    if chat.type == 'private' or chat.type == 'channel':
        return
    
    # 忽略管理员和机器人
    if user.is_bot:
        return
    
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return  # 管理员不受限制
    except:
        pass
    
    current_time = time.time()
    key = (chat.id, user.id)
    
    # 获取用户最近的消息时间
    message_times = user_message_times[key]
    
    # 添加当前消息时间
    message_times.append(current_time)
    
    # 检查是否在短时间内发送了太多消息
    if len(message_times) >= FLOOD_LIMIT:
        time_span = message_times[-1] - message_times[0]
        if time_span < FLOOD_WINDOW:
            try:
                # 删除消息
                await message.delete()
                
                # 警告用户
                warning_msg = await context.bot.send_message(
                    chat.id,
                    f"⚠️ {user.mention_html()} 请勿刷屏！消息已删除。",
                    parse_mode='HTML'
                )
                
                # 扣除积分
                db.subtract_points(chat.id, user.id, FLOOD_POINTS_PENALTY, "刷屏行为")
                
                # 5秒后删除警告消息
                import asyncio
                await asyncio.sleep(5)
                try:
                    await warning_msg.delete()
                except:
                    pass
                
                logger.info(f"检测到用户 {user.id} 在群组 {chat.id} 刷屏，已删除消息")
            except Exception as e:
                logger.error(f"防刷屏处理失败: {e}")


async def detect_duplicate_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """检测并删除重复消息"""
    if not update.message or not update.effective_chat:
        return
    
    chat = update.effective_chat
    message = update.message
    user = update.effective_user
    
    # 只处理群组消息（不包括频道和私聊）
    if chat.type == 'private' or chat.type == 'channel':
        return
    
    # 忽略管理员和机器人
    if user.is_bot:
        return
    
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return  # 管理员不受限制
    except:
        pass
    
    text = (message.text or message.caption or "").strip()
    
    if not text or len(text) < 10:  # 太短的消息不检测
        return
    
    key = (chat.id, user.id)
    message_texts = user_message_texts[key]
    
    # 检查是否与最近的消息重复
    if text in message_texts:
        try:
            # 删除重复消息
            await message.delete()
            
            # 扣除积分
            db.subtract_points(chat.id, user.id, DUPLICATE_POINTS_PENALTY, "发送重复消息")
            
            logger.info(f"检测到用户 {user.id} 在群组 {chat.id} 发送重复消息，已删除")
        except Exception as e:
            logger.error(f"删除重复消息失败: {e}")
    else:
        # 添加当前消息到历史记录
        message_texts.append(text)


"""
自动管理模块
包含自动删除广告、欢迎新成员等功能
"""
import re
import logging
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
from database import db
from config import (
    AUTO_DELETE_ADS, AUTO_WELCOME, NEW_MEMBER_BONUS,
    AD_POINTS_PENALTY
)
from utils_common import check_admin_permission
from error_handler import safe_execute

logger = logging.getLogger(__name__)

# 广告链接检测模式
AD_PATTERNS = [
    r'https?://t\.me/joinchat/',  # Telegram 群组邀请链接
    r'https?://t\.me/\+',  # Telegram 邀请链接
    r'https?://t\.me/c/\d+',  # Telegram 频道链接
    r'https?://(www\.)?(telegram|tg)\.(me|org)/',  # Telegram 相关链接
]

# 常见广告关键词（中文）
AD_KEYWORDS = [
    '加微信', '加QQ', '加群', '扫码进群', '扫码加群',
    '私聊我', '私我', '找我', '联系我',
    '代购', '代理', '批发', '优惠', '折扣',
    '刷单', '刷量', '刷粉', '刷赞',
    '兼职', '招聘', '招人', '工作',
    '贷款', '借钱', '放贷', '信用卡',
    '赌博', '博彩', '彩票', '投注',
]


def contains_ad_link(text: str) -> bool:
    """检测消息是否包含广告链接"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # 检查链接模式
    for pattern in AD_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    
    return False


def contains_ad_keywords(text: str) -> bool:
    """检测消息是否包含广告关键词"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # 检查关键词（至少匹配2个关键词才认为是广告）
    matched_keywords = [keyword for keyword in AD_KEYWORDS if keyword in text_lower]
    
    # 如果包含链接且有关键词，认为是广告
    if contains_ad_link(text) and len(matched_keywords) > 0:
        return True
    
    # 如果匹配多个关键词，认为是广告
    if len(matched_keywords) >= 2:
        return True
    
    return False


async def auto_delete_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """自动删除广告消息"""
    if not update.message or not update.effective_chat:
        return
    
    chat = update.effective_chat
    message = update.message
    user = update.effective_user
    
    # 只处理群组消息（不包括频道和私聊）
    if chat.type == 'private' or chat.type == 'channel':
        return
    
    # 检查是否启用自动删除广告（全局配置和群组配置）
    if not AUTO_DELETE_ADS or not db.is_auto_delete_ads_enabled(chat.id):
        return
    
    # 忽略管理员和机器人
    if user.is_bot:
        return
    
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return  # 管理员消息不删除
    except:
        pass
    
    # 检查消息文本
    text = message.text or message.caption or ""
    
    # 检测广告
    is_ad = False
    reason = ""
    
    if contains_ad_link(text):
        is_ad = True
        reason = "检测到广告链接"
    elif contains_ad_keywords(text):
        is_ad = True
        reason = "检测到广告关键词"
    
    # 如果检测到广告，删除消息并警告
    if is_ad:
        try:
            # 删除消息
            await message.delete()
            
            # 扣除积分（如果用户有积分）
            current_points = db.get_user_points(chat.id, user.id)
            if current_points > 0:
                points_deducted = min(AD_POINTS_PENALTY, current_points)
                db.subtract_points(chat.id, user.id, points_deducted, "发送广告")
            
            # 发送警告消息（可选，可以注释掉避免刷屏）
            # warning_msg = await context.bot.send_message(
            #     chat.id,
            #     f"⚠️ 已删除 {user.mention_html()} 的广告消息\n原因: {reason}",
            #     parse_mode='HTML'
            # )
            # # 5秒后删除警告消息
            # import asyncio
            # await asyncio.sleep(5)
            # try:
            #     await warning_msg.delete()
            # except:
            #     pass
            
            logger.info(f"自动删除用户 {user.id} 在群组 {chat.id} 的广告消息: {reason}")
        except Exception as e:
            logger.error(f"删除广告消息失败: {e}")


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """欢迎新成员"""
    if not update.message or not update.effective_chat:
        return
    
    chat = update.effective_chat
    
    # 只处理群组（不包括频道和私聊）
    if chat.type == 'private' or chat.type == 'channel':
        return
    
    # 检查是否有新成员加入
    if update.message.new_chat_members:
        for new_member in update.message.new_chat_members:
            # 忽略机器人
            if new_member.is_bot:
                continue
            
            try:
                # 检查是否启用欢迎消息
                if not db.is_welcome_enabled(chat.id):
                    return
                
                # 获取欢迎消息（从数据库或使用默认）
                welcome_text = db.get_welcome_message(chat.id)
                
                if not welcome_text:
                    # 默认欢迎消息
                    welcome_text = f"""
👋 欢迎 {new_member.mention_html()} 加入群组！

💡 请遵守群规，文明发言
💰 发言可以获得积分，使用 /points 查看
📊 使用 /top 查看积分排行榜

祝你在群里玩得开心！🎉
                    """
                
                # 替换占位符
                welcome_text = welcome_text.replace('{username}', new_member.mention_html())
                welcome_text = welcome_text.replace('{first_name}', new_member.first_name or '新成员')
                welcome_text = welcome_text.replace('{chat_title}', chat.title or '本群')
                
                # 发送欢迎消息
                await context.bot.send_message(
                    chat.id,
                    welcome_text,
                    parse_mode='HTML'
                )
                
                # 给新成员初始积分
                db.add_points(chat.id, new_member.id, NEW_MEMBER_BONUS, "新成员加入奖励")
                
                logger.info(f"欢迎新成员 {new_member.id} 加入群组 {chat.id}")
            except Exception as e:
                logger.error(f"欢迎新成员失败: {e}")


async def auto_kick_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """自动踢出新加入的机器人（可选功能）"""
    if not update.message or not update.effective_chat:
        return
    
    chat = update.effective_chat
    
    # 只处理群组
    if chat.type == 'private':
        return
    
    # 检查是否有新成员加入
    if update.message.new_chat_members:
        for new_member in update.message.new_chat_members:
            # 如果是机器人，自动踢出
            if new_member.is_bot and new_member.id != context.bot.id:
                try:
                    await context.bot.ban_chat_member(chat.id, new_member.id)
                    await context.bot.send_message(
                        chat.id,
                        f"🤖 已自动移除机器人: {new_member.mention_html()}",
                        parse_mode='HTML'
                    )
                    logger.info(f"自动踢出机器人 {new_member.id} 从群组 {chat.id}")
                except Exception as e:
                    logger.error(f"自动踢出机器人失败: {e}")


def get_welcome_message(chat_id: int) -> str:
    """从数据库获取群组的欢迎消息"""
    return db.get_welcome_message(chat_id)


def set_welcome_message(chat_id: int, message: str):
    """设置群组的欢迎消息"""
    db.set_welcome_message(chat_id, message)


"""
公共工具模块
统一管理所有模块共用的函数，避免代码重复
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
from functools import wraps
from typing import Optional

logger = logging.getLogger(__name__)

# 缓存管理员状态（减少API调用）
_admin_cache = {}
_cache_timeout = 300  # 缓存5分钟


async def check_admin_permission(update: Update, context: ContextTypes.DEFAULT_TYPE, use_cache: bool = True, allow_channel: bool = True) -> bool:
    """
    检查用户是否有管理员权限（统一函数，避免重复代码）
    支持群组和频道
    
    Args:
        update: Telegram Update 对象
        context: Context 对象
        use_cache: 是否使用缓存（默认True）
        allow_channel: 是否允许频道（默认True）
    
    Returns:
        bool: 如果是管理员返回True，否则返回False
    """
    user = update.effective_user
    chat = update.effective_chat
    
    if not chat or chat.type == 'private':
        return False
    
    # 频道支持
    if chat.type == 'channel':
        if not allow_channel:
            return False
        # 频道需要检查是否是管理员
        try:
            member = await context.bot.get_chat_member(chat.id, user.id)
            return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        except Exception as e:
            logger.error(f"检查频道管理员权限时出错: {e}")
            return False
    
    if not user:
        return False
    
    # 检查缓存
    cache_key = (chat.id, user.id)
    if use_cache and cache_key in _admin_cache:
        cached_result, cached_time = _admin_cache[cache_key]
        import time
        if time.time() - cached_time < _cache_timeout:
            return cached_result
    
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
        
        # 更新缓存
        if use_cache:
            import time
            _admin_cache[cache_key] = (is_admin, time.time())
        
        return is_admin
    except Exception as e:
        logger.error(f"检查管理员权限时出错: {e}")
        return False


def require_admin(func):
    """
    装饰器：要求管理员权限才能执行函数
    使用示例:
        @require_admin
        async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            ...
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not await check_admin_permission(update, context):
            await update.message.reply_text("❌ 您没有权限使用此命令！")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def require_group(func):
    """
    装饰器：要求必须在群组中使用（不包括频道）
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat = update.effective_chat
        if not chat or chat.type == 'private':
            await update.message.reply_text("❌ 此命令只能在群组中使用！")
            return
        if chat.type == 'channel':
            await update.message.reply_text("❌ 此命令只能在群组中使用，频道不支持此功能！")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def require_channel_or_group(func):
    """
    装饰器：要求必须在群组或频道中使用
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat = update.effective_chat
        if not chat or chat.type == 'private':
            await update.message.reply_text("❌ 此命令只能在群组或频道中使用！")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def require_channel(func):
    """
    装饰器：要求必须在频道中使用
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat = update.effective_chat
        if not chat or chat.type != 'channel':
            await update.message.reply_text("❌ 此命令只能在频道中使用！")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def require_reply(func):
    """
    装饰器：要求必须回复消息
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        message = update.message
        if not message or not message.reply_to_message:
            await message.reply_text("⚠️ 请回复要操作的消息！")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def clear_admin_cache(chat_id: Optional[int] = None, user_id: Optional[int] = None):
    """
    清除管理员权限缓存
    
    Args:
        chat_id: 群组ID，如果提供则只清除该群组的缓存
        user_id: 用户ID，如果提供则只清除该用户的缓存
    """
    global _admin_cache
    
    if chat_id is None and user_id is None:
        # 清除所有缓存
        _admin_cache.clear()
    else:
        # 清除特定缓存
        keys_to_remove = []
        for key in _admin_cache.keys():
            cid, uid = key
            if (chat_id is None or cid == chat_id) and (user_id is None or uid == user_id):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del _admin_cache[key]
    
    logger.debug(f"已清除管理员缓存: chat_id={chat_id}, user_id={user_id}")


def safe_delete_message(bot, chat_id: int, message_id: int):
    """
    安全删除消息（带错误处理）
    
    Args:
        bot: Bot 实例
        chat_id: 群组ID
        message_id: 消息ID
    
    Returns:
        bool: 删除成功返回True，失败返回False
    """
    import asyncio
    
    async def _delete():
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            return True
        except Exception as e:
            logger.warning(f"删除消息失败: {e}")
            return False
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，创建任务
            task = asyncio.create_task(_delete())
            return task
        else:
            # 如果事件循环未运行，直接运行
            return loop.run_until_complete(_delete())
    except Exception as e:
        logger.error(f"删除消息时出错: {e}")
        return False


def format_time(seconds: int) -> str:
    """
    格式化时间（秒转换为可读格式）
    
    Args:
        seconds: 秒数
    
    Returns:
        str: 格式化后的时间字符串
    """
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分钟"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours}小时"
    else:
        days = seconds // 86400
        return f"{days}天"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后的后缀
    
    Returns:
        str: 截断后的文本
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_time_string(time_str: str) -> Optional[int]:
    """
    解析时间字符串为秒数
    支持格式: 1h, 30m, 60s, 1d 等
    
    Args:
        time_str: 时间字符串
    
    Returns:
        int: 秒数，解析失败返回None
    """
    if not time_str:
        return None
    
    time_str = time_str.strip().lower()
    
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
    }
    
    try:
        # 尝试直接解析为数字（秒）
        return int(time_str)
    except ValueError:
        pass
    
    # 尝试解析带单位的时间
    for unit, multiplier in multipliers.items():
        if time_str.endswith(unit):
            try:
                value = int(time_str[:-1])
                return value * multiplier
            except ValueError:
                pass
    
    return None


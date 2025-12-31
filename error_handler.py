"""
错误处理模块
统一处理各种错误和异常
"""
import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

# 兼容不同版本的异常类导入
try:
    from telegram.error import (
        NetworkError,
        TimedOut,
        RetryAfter,
        BadRequest,
        Unauthorized,
        Conflict
    )
except ImportError:
    # 如果导入失败，使用基类并通过错误消息判断
    NetworkError = TimedOut = RetryAfter = BadRequest = Unauthorized = Conflict = TelegramError


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    全局错误处理器
    统一处理所有异常和错误
    """
    error = context.error
    
    if not error:
        return
    
    # 记录错误详情
    logger.error(f"发生错误: {error}", exc_info=error)
    
    # 根据错误类型进行不同处理
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # 速率限制
    if 'retry_after' in error_str or 'RetryAfter' in error_type:
        if hasattr(error, 'retry_after'):
            logger.warning(f"速率限制，需要等待 {error.retry_after} 秒")
        else:
            logger.warning(f"速率限制: {error}")
        return
    
    # 未授权错误（Token错误等）
    if 'unauthorized' in error_str or 'Unauthorized' in error_type:
        logger.critical(f"未授权错误: {error}")
        return
    
    # 请求错误
    if 'bad request' in error_str or 'BadRequest' in error_type:
        logger.warning(f"请求错误: {error}")
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ 操作失败，请检查参数是否正确。"
                )
            except:
                pass
        return
    
    # 网络错误
    if 'network' in error_str or 'NetworkError' in error_type:
        logger.warning(f"网络错误: {error}")
        return
    
    # 超时错误
    if 'timeout' in error_str or 'TimedOut' in error_type:
        logger.warning(f"请求超时: {error}")
        return
    
    # 冲突错误
    if 'conflict' in error_str or 'Conflict' in error_type:
        logger.critical(f"冲突错误: {error}")
        return
    
    # 其他 Telegram 错误
    if isinstance(error, TelegramError):
        logger.error(f"Telegram 错误: {error}")
    
    else:
        # 未知错误
        logger.error(f"未知错误: {error}")
        logger.error(traceback.format_exc())
        
        # 尝试向用户发送错误消息
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ 发生未知错误，请稍后重试。"
                )
            except:
                pass


def safe_execute(func):
    """
    装饰器：安全执行函数，捕获所有异常
    
    使用示例:
        @safe_execute
        async def my_function():
            ...
    """
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"执行函数 {func.__name__} 时出错: {e}", exc_info=e)
            return None
    
    return wrapper


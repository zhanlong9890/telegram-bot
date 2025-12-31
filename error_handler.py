"""
错误处理模块
统一处理各种错误和异常
"""
import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import (
    TelegramError,
    NetworkError,
    TimedOut,
    RetryAfter,
    BadRequest,
    Unauthorized,
    Conflict
)

logger = logging.getLogger(__name__)


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
    if isinstance(error, RetryAfter):
        # 速率限制，等待后重试
        logger.warning(f"速率限制，需要等待 {error.retry_after} 秒")
        return
    
    elif isinstance(error, Unauthorized):
        # 未授权错误（Token错误等）
        logger.critical(f"未授权错误: {error}")
        return
    
    elif isinstance(error, BadRequest):
        # 请求错误（可能是参数错误）
        logger.warning(f"请求错误: {error}")
        
        # 尝试向用户发送友好错误消息
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ 操作失败，请检查参数是否正确。"
                )
            except:
                pass
    
    elif isinstance(error, NetworkError):
        # 网络错误
        logger.warning(f"网络错误: {error}")
        # 网络错误通常是暂时的，不需要通知用户
    
    elif isinstance(error, TimedOut):
        # 超时错误
        logger.warning(f"请求超时: {error}")
    
    elif isinstance(error, Conflict):
        # 冲突错误（可能是多个实例同时运行）
        logger.critical(f"冲突错误: {error}")
    
    elif isinstance(error, TelegramError):
        # 其他 Telegram 错误
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


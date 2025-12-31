"""
性能优化模块
包含缓存、连接池等性能优化功能
"""
import time
import functools
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class Cache:
    """简单的内存缓存实现"""
    
    def __init__(self, default_timeout: int = 300):
        """
        初始化缓存
        
        Args:
            default_timeout: 默认超时时间（秒）
        """
        self._cache = {}
        self.default_timeout = default_timeout
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值，如果不存在或已过期返回None
        """
        if key not in self._cache:
            return None
        
        value, expire_time = self._cache[key]
        
        if time.time() > expire_time:
            # 已过期，删除
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            timeout: 超时时间（秒），None使用默认值
        """
        timeout = timeout or self.default_timeout
        expire_time = time.time() + timeout
        self._cache[key] = (value, expire_time)
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """清空所有缓存"""
        self._cache.clear()
    
    def cleanup(self):
        """清理过期缓存"""
        current_time = time.time()
        keys_to_delete = [
            key for key, (_, expire_time) in self._cache.items()
            if current_time > expire_time
        ]
        for key in keys_to_delete:
            del self._cache[key]


# 全局缓存实例
cache = Cache(default_timeout=300)


def cached(timeout: int = 300):
    """
    缓存装饰器
    
    Args:
        timeout: 缓存超时时间（秒）
    
    使用示例:
        @cached(timeout=60)
        async def expensive_function(arg1, arg2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


def measure_time(func: Callable) -> Callable:
    """
    测量函数执行时间的装饰器
    
    使用示例:
        @measure_time
        async def my_function():
            ...
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed_time = time.time() - start_time
            if elapsed_time > 1.0:  # 只记录超过1秒的操作
                logger.warning(f"函数 {func.__name__} 执行时间: {elapsed_time:.2f}秒")
    
    return wrapper


"""
简单内存缓存装饰器
用于缓存高频查询结果，减少数据库压力
"""
import time
from functools import wraps
from typing import Any, Callable, Optional


class SimpleCache:
    """简单内存缓存实现"""
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl  # 默认5分钟过期
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，如果过期或不存在返回None"""
        if key not in self._cache:
            return None
        
        value, expire_at = self._cache[key]
        if time.time() > expire_at:
            # 过期了，删除缓存
            del self._cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        # 如果缓存满了，删除最旧的一个
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        expire_at = time.time() + (ttl if ttl is not None else self._default_ttl)
        self._cache[key] = (value, expire_at)
    
    def delete(self, key: str) -> None:
        """删除指定缓存"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()


# 全局缓存实例
cache = SimpleCache(max_size=100, default_ttl=300)


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    缓存装饰器
    
    参数:
        ttl: 缓存过期时间（秒），默认使用全局配置
        key_prefix: 缓存key前缀
    
    使用:
        @cached(ttl=600)  # 缓存10分钟
        def get_hot_schools():
            return fetch_all("SELECT ...")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 构建缓存key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        # 暴露缓存操作方法
        wrapper.cache_delete = lambda: cache.delete(cache_key) if 'cache_key' in locals() else None
        wrapper.cache_clear = lambda: cache.clear()
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    批量删除匹配模式的缓存
    
    参数:
        pattern: 匹配模式（支持前缀匹配）
    
    返回:
        删除的缓存数量
    """
    keys_to_delete = [key for key in cache._cache.keys() if key.startswith(pattern)]
    for key in keys_to_delete:
        del cache._cache[key]
    return len(keys_to_delete)

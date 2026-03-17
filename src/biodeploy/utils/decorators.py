"""
工具函数模块

提供常用的工具函数和装饰器。
"""

import functools
import time
from typing import Any, Callable, Optional, TypeVar, cast
from biodeploy.infrastructure.logger import get_logger

F = TypeVar('F', bound=Callable[..., Any])


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """重试装饰器
    
    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的增长因子
        exceptions: 需要重试的异常类型
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger("retry")
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{current_delay:.1f}秒后重试"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        
        return cast(F, wrapper)
    
    return decorator


def timing(func: F) -> F:
    """计时装饰器
    
    记录函数执行时间
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger("timing")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.info(f"函数 {func.__name__} 执行耗时: {elapsed_time:.2f}秒")
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"函数 {func.__name__} 执行失败 (耗时: {elapsed_time:.2f}秒): {e}")
            raise
    
    return cast(F, wrapper)


def log_call(func: F) -> F:
    """日志记录装饰器
    
    记录函数调用和返回值
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger("call")
        
        # 记录调用
        args_str = ", ".join([repr(a) for a in args])
        kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        
        logger.debug(f"调用 {func.__name__}({all_args})")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} 返回: {repr(result)}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} 抛出异常: {e}")
            raise
    
    return cast(F, wrapper)


def validate_types(**validators):
    """类型验证装饰器
    
    验证函数参数类型
    
    Args:
        validators: 参数名到验证函数的映射
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取参数绑定
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # 验证参数
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        raise ValueError(
                            f"参数 {param_name} 的值 {value} 未通过验证"
                        )
            
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator


def singleton(cls):
    """单例装饰器
    
    确保类只有一个实例
    
    Args:
        cls: 要装饰的类
        
    Returns:
        装饰后的类
    """
    instances = {}
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def deprecated(message: str = None):
    """废弃警告装饰器
    
    标记函数为废弃状态
    
    Args:
        message: 废弃消息
        
    Returns:
        装饰器函数
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            msg = message or f"函数 {func.__name__} 已废弃"
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator


class cached_property:
    """缓存属性装饰器
    
    缓存属性计算结果，避免重复计算
    """
    
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__
    
    def __get__(self, obj, cls):
        if obj is None:
            return self
        
        value = self.func(obj)
        obj.__dict__[self.func.__name__] = value
        return value

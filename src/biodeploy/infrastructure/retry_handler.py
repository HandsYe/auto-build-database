"""
重试处理器

提供带重试机制的函数执行功能，支持指数退避算法。
"""

import time
from functools import wraps
from typing import Any, Callable, Optional, Tuple, TypeVar

T = TypeVar("T")


class RetryHandler:
    """重试处理器

    提供带重试机制的函数执行功能，支持多种重试策略。
    """

    @staticmethod
    def retry(
        max_attempts: int = 3,
        backoff_factor: float = 1.0,
        max_delay: float = 60.0,
        exceptions: Tuple[type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable[[Exception, int], None]] = None,
        should_retry: Optional[Callable[[Exception], bool]] = None,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]:
        """重试装饰器

        Args:
            max_attempts: 最大重试次数
            backoff_factor: 退避因子
            max_delay: 最大延迟时间（秒）
            exceptions: 需要重试的异常类型
            on_retry: 每次重试时的回调函数
            should_retry: 判断是否应该重试的函数

        Returns:
            装饰器函数
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                last_exception: Optional[Exception] = None

                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e

                        # 检查是否应该重试
                        if should_retry and not should_retry(e):
                            raise

                        # 如果是最后一次尝试，抛出异常
                        if attempt == max_attempts - 1:
                            raise

                        # 计算延迟时间（指数退避）
                        delay = min(
                            backoff_factor * (2 ** attempt),
                            max_delay,
                        )

                        # 调用重试回调
                        if on_retry:
                            on_retry(e, attempt + 1)

                        # 等待后重试
                        time.sleep(delay)

                # 理论上不会到达这里，但为了类型检查
                if last_exception:
                    raise last_exception
                raise RuntimeError("Unexpected error in retry logic")

            return wrapper
        return decorator

    @staticmethod
    def execute(
        func: Callable[..., T],
        max_attempts: int = 3,
        backoff_factor: float = 1.0,
        max_delay: float = 60.0,
        exceptions: Tuple[type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable[[Exception, int], None]] = None,
        should_retry: Optional[Callable[[Exception], bool]] = None,
        *args,
        **kwargs,
    ) -> T:
        """执行函数，失败时重试

        Args:
            func: 要执行的函数
            max_attempts: 最大重试次数
            backoff_factor: 退避因子
            max_delay: 最大延迟时间（秒）
            exceptions: 需要重试的异常类型
            on_retry: 每次重试时的回调函数
            should_retry: 判断是否应该重试的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果

        Raises:
            最后一次重试的异常
        """
        last_exception: Optional[Exception] = None

        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e

                # 检查是否应该重试
                if should_retry and not should_retry(e):
                    raise

                # 如果是最后一次尝试，抛出异常
                if attempt == max_attempts - 1:
                    raise

                # 计算延迟时间（指数退避）
                delay = min(
                    backoff_factor * (2 ** attempt),
                    max_delay,
                )

                # 调用重试回调
                if on_retry:
                    on_retry(e, attempt + 1)

                # 等待后重试
                time.sleep(delay)

        # 理论上不会到达这里
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry logic")


# 便捷装饰器
def retry(
    max_attempts: int = 3,
    backoff_factor: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    should_retry: Optional[Callable[[Exception], bool]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """重试装饰器（便捷函数）

    Args:
        max_attempts: 最大重试次数
        backoff_factor: 退避因子
        max_delay: 最大延迟时间（秒）
        exceptions: 需要重试的异常类型
        on_retry: 每次重试时的回调函数
        should_retry: 判断是否应该重试的函数

    Returns:
        装饰器函数
    """
    return RetryHandler.retry(
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        max_delay=max_delay,
        exceptions=exceptions,
        on_retry=on_retry,
        should_retry=should_retry,
    )

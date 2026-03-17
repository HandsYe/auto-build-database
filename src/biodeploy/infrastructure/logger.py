"""
日志系统

提供统一的日志记录功能。
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional


class Logger:
    """日志系统

    提供统一的日志记录功能，支持文件滚动和多种日志级别。

    Attributes:
        DEFAULT_FORMAT: 默认日志格式
        DEFAULT_MAX_SIZE: 默认日志文件最大大小
        DEFAULT_BACKUP_COUNT: 默认日志备份数量
    """

    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_MAX_SIZE = 100 * 1024 * 1024  # 100MB
    DEFAULT_BACKUP_COUNT = 5

    def __init__(self) -> None:
        """初始化日志系统"""
        self._loggers: Dict[str, logging.Logger] = {}
        self._initialized = False

    def setup(
        self,
        level: str = "INFO",
        log_path: Optional[Path] = None,
        log_format: Optional[str] = None,
        max_size: Optional[int] = None,
        backup_count: Optional[int] = None,
    ) -> logging.Logger:
        """设置日志系统

        Args:
            level: 日志级别
            log_path: 日志文件路径，如果为None则只输出到控制台
            log_format: 日志格式
            max_size: 日志文件最大大小（字节）
            backup_count: 日志备份数量

        Returns:
            根日志记录器
        """
        # 获取根日志记录器
        root_logger = logging.getLogger("biodeploy")

        # 清除现有的处理器
        root_logger.handlers.clear()

        # 设置日志级别
        root_logger.setLevel(getattr(logging, level.upper()))

        # 创建格式化器
        formatter = logging.Formatter(log_format or self.DEFAULT_FORMAT)

        # 添加控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # 添加文件处理器（如果指定了日志文件路径）
        if log_path:
            # 确保日志目录存在
            log_path = Path(log_path)
            log_path.mkdir(parents=True, exist_ok=True)

            # 创建日志文件路径
            log_file = log_path / "biodeploy.log"

            # 创建滚动文件处理器
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_size or self.DEFAULT_MAX_SIZE,
                backupCount=backup_count or self.DEFAULT_BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        self._initialized = True
        self._loggers["biodeploy"] = root_logger

        return root_logger

    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器

        Args:
            name: 日志记录器名称

        Returns:
            日志记录器
        """
        if not self._initialized:
            self.setup()

        if name not in self._loggers:
            # 创建子日志记录器
            logger = logging.getLogger(f"biodeploy.{name}")
            self._loggers[name] = logger

        return self._loggers[name]

    def set_level(self, level: str) -> None:
        """设置日志级别

        Args:
            level: 日志级别
        """
        if not self._initialized:
            self.setup()

        root_logger = self._loggers.get("biodeploy")
        if root_logger:
            root_logger.setLevel(getattr(logging, level.upper()))
            for handler in root_logger.handlers:
                handler.setLevel(getattr(logging, level.upper()))


# 全局日志管理器实例
_logger_manager = Logger()


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return _logger_manager.get_logger(name)


def setup_logging(
    level: str = "INFO",
    log_path: Optional[Path] = None,
    log_format: Optional[str] = None,
    max_size: Optional[int] = None,
    backup_count: Optional[int] = None,
) -> logging.Logger:
    """设置日志系统

    Args:
        level: 日志级别
        log_path: 日志文件路径
        log_format: 日志格式
        max_size: 日志文件最大大小
        backup_count: 日志备份数量

    Returns:
        根日志记录器
    """
    return _logger_manager.setup(level, log_path, log_format, max_size, backup_count)

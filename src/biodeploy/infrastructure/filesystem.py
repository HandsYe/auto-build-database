"""
文件系统工具

提供文件系统操作的工具函数。
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Optional

from biodeploy.infrastructure.logger import get_logger


class FileSystem:
    """文件系统工具

    提供文件和目录操作的实用工具函数。
    """

    @staticmethod
    def ensure_directory(path: Path) -> None:
        """确保目录存在

        如果目录不存在，则创建它。

        Args:
            path: 目录路径
        """
        path = Path(path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            get_logger("filesystem").debug(f"创建目录: {path}")

    @staticmethod
    def get_disk_usage(path: Path) -> Dict[str, int]:
        """获取磁盘使用情况

        Args:
            path: 路径

        Returns:
            包含磁盘使用情况的字典，包括 total, used, free 字段
        """
        path = Path(path)
        if not path.exists():
            path = path.parent

        usage = shutil.disk_usage(path)
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
        }

    @staticmethod
    def check_permissions(path: Path, mode: int = os.W_OK) -> bool:
        """检查路径权限

        Args:
            path: 路径
            mode: 权限模式，默认为写权限

        Returns:
            如果有权限返回True，否则返回False
        """
        path = Path(path)
        return os.access(path, mode)

    @staticmethod
    def check_disk_space(path: Path, required_size: int) -> bool:
        """检查磁盘空间是否足够

        Args:
            path: 路径
            required_size: 需要的空间大小（字节）

        Returns:
            如果空间足够返回True，否则返回False
        """
        usage = FileSystem.get_disk_usage(path)
        return usage["free"] >= required_size

    @staticmethod
    def safe_remove(path: Path) -> bool:
        """安全删除文件或目录

        Args:
            path: 文件或目录路径

        Returns:
            如果成功删除返回True，否则返回False
        """
        path = Path(path)
        logger = get_logger("filesystem")

        if not path.exists():
            logger.debug(f"路径不存在，无需删除: {path}")
            return True

        try:
            if path.is_file() or path.is_symlink():
                path.unlink()
                logger.debug(f"删除文件: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                logger.debug(f"删除目录: {path}")
            return True

        except Exception as e:
            logger.error(f"删除失败: {path}, 错误: {e}")
            return False

    @staticmethod
    def copy_file(src: Path, dst: Path, preserve_metadata: bool = True) -> bool:
        """复制文件

        Args:
            src: 源文件路径
            dst: 目标文件路径
            preserve_metadata: 是否保留元数据

        Returns:
            如果成功复制返回True，否则返回False
        """
        src = Path(src)
        dst = Path(dst)
        logger = get_logger("filesystem")

        if not src.exists():
            logger.error(f"源文件不存在: {src}")
            return False

        try:
            # 确保目标目录存在
            dst.parent.mkdir(parents=True, exist_ok=True)

            # 复制文件
            if preserve_metadata:
                shutil.copy2(src, dst)
            else:
                shutil.copy(src, dst)

            logger.debug(f"复制文件: {src} -> {dst}")
            return True

        except Exception as e:
            logger.error(f"复制文件失败: {src} -> {dst}, 错误: {e}")
            return False

    @staticmethod
    def move_file(src: Path, dst: Path) -> bool:
        """移动文件

        Args:
            src: 源文件路径
            dst: 目标文件路径

        Returns:
            如果成功移动返回True，否则返回False
        """
        src = Path(src)
        dst = Path(dst)
        logger = get_logger("filesystem")

        if not src.exists():
            logger.error(f"源文件不存在: {src}")
            return False

        try:
            # 确保目标目录存在
            dst.parent.mkdir(parents=True, exist_ok=True)

            # 移动文件
            shutil.move(str(src), str(dst))

            logger.debug(f"移动文件: {src} -> {dst}")
            return True

        except Exception as e:
            logger.error(f"移动文件失败: {src} -> {dst}, 错误: {e}")
            return False

    @staticmethod
    def get_file_size(path: Path) -> int:
        """获取文件大小

        Args:
            path: 文件路径

        Returns:
            文件大小（字节），如果文件不存在返回0
        """
        path = Path(path)
        if not path.exists() or not path.is_file():
            return 0

        return path.stat().st_size

    @staticmethod
    def get_directory_size(path: Path) -> int:
        """获取目录大小

        Args:
            path: 目录路径

        Returns:
            目录大小（字节），如果目录不存在返回0
        """
        path = Path(path)
        if not path.exists() or not path.is_dir():
            return 0

        total_size = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size

    @staticmethod
    def list_files(
        path: Path, pattern: str = "*", recursive: bool = False
    ) -> list[Path]:
        """列出文件

        Args:
            path: 目录路径
            pattern: 文件模式
            recursive: 是否递归列出

        Returns:
            文件路径列表
        """
        path = Path(path)
        if not path.exists() or not path.is_dir():
            return []

        if recursive:
            return list(path.rglob(pattern))
        else:
            return list(path.glob(pattern))

    @staticmethod
    def create_symlink(src: Path, dst: Path, force: bool = False) -> bool:
        """创建符号链接

        Args:
            src: 源路径
            dst: 目标链接路径
            force: 如果目标存在是否强制覆盖

        Returns:
            如果成功创建返回True，否则返回False
        """
        src = Path(src)
        dst = Path(dst)
        logger = get_logger("filesystem")

        if not src.exists():
            logger.error(f"源路径不存在: {src}")
            return False

        try:
            # 如果目标存在且需要强制覆盖
            if dst.exists() or dst.is_symlink():
                if force:
                    dst.unlink()
                else:
                    logger.error(f"目标路径已存在: {dst}")
                    return False

            # 创建符号链接
            dst.symlink_to(src)

            logger.debug(f"创建符号链接: {src} -> {dst}")
            return True

        except Exception as e:
            logger.error(f"创建符号链接失败: {src} -> {dst}, 错误: {e}")
            return False

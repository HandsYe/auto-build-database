"""
状态管理器

管理数据库安装状态的查询和更新。
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from biodeploy.infrastructure.logger import get_logger
from biodeploy.infrastructure.state_storage import StateStorage
from biodeploy.models.state import InstallationRecord, InstallationStatus


class StateManager:
    """状态管理器

    负责管理数据库安装状态的查询、更新和版本切换。
    """

    def __init__(self, state_path: Optional[Path] = None):
        """初始化状态管理器

        Args:
            state_path: 状态文件路径
        """
        self._storage = StateStorage(state_path)
        self._logger = get_logger("state_manager")

    def get_installed_databases(self) -> List[InstallationRecord]:
        """获取所有已安装的数据库

        Returns:
            已安装数据库列表
        """
        return self._storage.get_installed_databases()

    def get_database_info(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional[InstallationRecord]:
        """获取数据库信息

        Args:
            name: 数据库名称
            version: 数据库版本，如果为None则返回最新版本

        Returns:
            安装记录，如果未找到返回None
        """
        return self._storage.load(name, version)

    def get_database_versions(self, name: str) -> List[InstallationRecord]:
        """获取数据库的所有版本

        Args:
            name: 数据库名称

        Returns:
            该数据库的所有版本记录列表
        """
        return self._storage.load_by_name(name)

    def update_status(
        self,
        name: str,
        version: str,
        status: InstallationStatus,
        progress: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """更新数据库状态

        Args:
            name: 数据库名称
            version: 数据库版本
            status: 新状态
            progress: 进度 (0.0 - 1.0)
            error_message: 错误信息

        Returns:
            如果更新成功返回True，否则返回False
        """
        return self._storage.update_status(name, version, status, progress, error_message)

    def save_record(self, record: InstallationRecord) -> None:
        """保存安装记录

        Args:
            record: 安装记录
        """
        self._storage.save(record)
        self._logger.info(f"保存安装记录: {record.name} {record.version}")

    def remove_record(self, name: str, version: Optional[str] = None) -> bool:
        """移除安装记录

        Args:
            name: 数据库名称
            version: 数据库版本，如果为None则移除所有版本

        Returns:
            如果移除成功返回True，否则返回False
        """
        return self._storage.remove(name, version)

    def is_installed(self, name: str, version: Optional[str] = None) -> bool:
        """检查数据库是否已安装

        Args:
            name: 数据库名称
            version: 数据库版本，如果为None则检查任何版本

        Returns:
            如果已安装返回True，否则返回False
        """
        record = self._storage.load(name, version)
        if record is None:
            return False
        return record.status == InstallationStatus.COMPLETED

    def switch_version(self, name: str, version: str) -> bool:
        """切换数据库版本

        通过创建符号链接切换默认版本。

        Args:
            name: 数据库名称
            version: 目标版本

        Returns:
            如果切换成功返回True，否则返回False
        """
        try:
            # 检查目标版本是否已安装
            target_record = self._storage.load(name, version)
            if not target_record or target_record.status != InstallationStatus.COMPLETED:
                self._logger.error(f"版本 {version} 未安装")
                return False

            # 创建符号链接指向目标版本
            # 假设默认版本链接在安装路径的父目录
            default_link = target_record.install_path.parent / name

            # 移除现有的默认链接
            if default_link.exists() or default_link.is_symlink():
                default_link.unlink()

            # 创建新的符号链接
            default_link.symlink_to(target_record.install_path)

            self._logger.info(f"切换到版本 {version}: {default_link} -> {target_record.install_path}")
            return True

        except Exception as e:
            self._logger.error(f"切换版本失败: {e}")
            return False

    def check_integrity(self, name: str, version: Optional[str] = None) -> bool:
        """检查数据库完整性

        Args:
            name: 数据库名称
            version: 数据库版本，如果为None则检查最新版本

        Returns:
            如果完整返回True，否则返回False
        """
        record = self._storage.load(name, version)
        if not record:
            return False

        # 检查安装路径是否存在
        if not record.install_path.exists():
            self._logger.warning(f"安装路径不存在: {record.install_path}")
            return False

        # 检查关键文件是否存在
        for file_path in record.files:
            if not file_path.exists():
                self._logger.warning(f"文件缺失: {file_path}")
                return False

        return True

    def get_status_summary(self) -> Dict[str, any]:
        """获取状态摘要

        Returns:
            状态摘要字典
        """
        all_records = self._storage.load_all()

        total = len(all_records)
        completed = sum(1 for r in all_records if r.status == InstallationStatus.COMPLETED)
        failed = sum(1 for r in all_records if r.status == InstallationStatus.FAILED)
        in_progress = sum(1 for r in all_records if r.is_in_progress())

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "databases": [r.name for r in all_records],
        }

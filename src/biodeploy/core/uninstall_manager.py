"""
卸载管理器

处理数据库的卸载操作。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from biodeploy.adapters.adapter_registry import AdapterRegistry
from biodeploy.infrastructure.filesystem import FileSystem
from biodeploy.infrastructure.logger import get_logger
from biodeploy.models.state import InstallationRecord, InstallationStatus
from biodeploy.services.environment_service import EnvironmentService
from biodeploy.core.state_manager import StateManager


class UninstallManager:
    """卸载管理器

    负责卸载数据库并清理相关配置。
    """

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        registry: Optional[AdapterRegistry] = None,
    ):
        """初始化卸载管理器

        Args:
            state_manager: 状态管理器
            registry: 适配器注册表
        """
        self._state_manager = state_manager or StateManager()
        self._registry = registry or AdapterRegistry()
        self._env_service = EnvironmentService()
        self._logger = get_logger("uninstall_manager")

    def uninstall(
        self,
        name: str,
        version: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """卸载数据库

        Args:
            name: 数据库名称
            version: 数据库版本，如果为None则卸载所有版本
            options: 卸载选项
                - keep_config: 是否保留配置文件
                - force: 是否强制卸载

        Returns:
            如果卸载成功返回True，否则返回False
        """
        options = options or {}
        keep_config = options.get("keep_config", False)
        force = options.get("force", False)

        # 获取安装记录
        if version:
            records = [self._state_manager.get_database_info(name, version)]
            records = [r for r in records if r]
        else:
            records = self._state_manager.get_database_versions(name)

        if not records:
            self._logger.warning(f"未找到安装记录: {name}")
            return True

        success = True
        for record in records:
            if not self._uninstall_single(record, keep_config, force):
                success = False

        return success

    def _uninstall_single(
        self,
        record: InstallationRecord,
        keep_config: bool,
        force: bool,
    ) -> bool:
        """卸载单个数据库版本

        Args:
            record: 安装记录
            keep_config: 是否保留配置文件
            force: 是否强制卸载

        Returns:
            如果卸载成功返回True，否则返回False
        """
        name = record.name
        version = record.version
        install_path = record.install_path

        self._logger.info(f"开始卸载 {name} {version}")

        try:
            # 获取适配器
            adapter = self._registry.get(name)

            # 使用适配器的卸载方法
            if adapter:
                if not adapter.uninstall(install_path):
                    if not force:
                        self._logger.error(f"适配器卸载失败: {name}")
                        return False
                    self._logger.warning(f"适配器卸载失败，强制继续: {name}")

            # 清理配置文件（如果不保留）
            if not keep_config:
                self._clean_config_files(record)

            # 清理环境变量
            self._env_service.remove_from_shell_config(record)

            # 移除安装记录
            self._state_manager.remove_record(name, version)

            self._logger.info(f"卸载完成: {name} {version}")
            return True

        except Exception as e:
            self._logger.error(f"卸载失败: {e}")
            if force:
                # 强制模式下，即使出错也移除记录
                self._state_manager.remove_record(name, version)
                return True
            return False

    def _clean_config_files(self, record: InstallationRecord) -> None:
        """清理配置文件

        Args:
            record: 安装记录
        """
        for config_file in record.config_files:
            try:
                FileSystem.safe_remove(config_file)
                self._logger.debug(f"删除配置文件: {config_file}")
            except Exception as e:
                self._logger.warning(f"删除配置文件失败: {config_file} - {e}")

    def uninstall_multiple(
        self,
        names: List[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """批量卸载多个数据库

        Args:
            names: 数据库名称列表
            options: 卸载选项

        Returns:
            数据库名称到卸载结果的映射
        """
        results = {}
        for name in names:
            results[name] = self.uninstall(name, None, options)
        return results

    def clean_orphaned_records(self) -> List[str]:
        """清理孤立的安装记录

        删除那些安装路径已不存在但状态记录仍存在的记录。

        Returns:
            已清理的数据库名称列表
        """
        cleaned = []
        all_records = self._state_manager._storage.load_all()

        for record in all_records:
            if not record.install_path.exists():
                self._logger.info(f"清理孤立记录: {record.name} {record.version}")
                self._state_manager.remove_record(record.name, record.version)
                cleaned.append(record.name)

        return cleaned

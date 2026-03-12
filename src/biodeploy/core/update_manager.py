"""
更新管理器

处理数据库的更新检查和升级操作。
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from biodeploy.adapters.adapter_registry import AdapterRegistry
from biodeploy.adapters.base_adapter import BaseAdapter
from biodeploy.infrastructure.filesystem import FileSystem
from biodeploy.infrastructure.logger import get_logger
from biodeploy.models.state import InstallationRecord, InstallationStatus
from biodeploy.core.state_manager import StateManager


@dataclass
class UpdateInfo:
    """更新信息"""
    name: str
    current_version: str
    latest_version: str
    has_update: bool
    download_size: int
    release_notes: Optional[str] = None


class UpdateManager:
    """更新管理器

    负责检查数据库更新和执行升级操作。
    """

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        registry: Optional[AdapterRegistry] = None,
    ):
        """初始化更新管理器

        Args:
            state_manager: 状态管理器
            registry: 适配器注册表
        """
        self._state_manager = state_manager or StateManager()
        self._registry = registry or AdapterRegistry()
        self._logger = get_logger("update_manager")

    def check_update(self, name: str) -> Optional[UpdateInfo]:
        """检查单个数据库是否有更新

        Args:
            name: 数据库名称

        Returns:
            更新信息，如果没有更新或数据库不存在返回None
        """
        # 获取当前安装记录
        current_record = self._state_manager.get_database_info(name)
        if not current_record:
            self._logger.warning(f"数据库未安装: {name}")
            return None

        # 获取适配器
        adapter = self._registry.get(name)
        if not adapter:
            self._logger.error(f"未找到适配器: {name}")
            return None

        # 获取最新版本
        latest_version = adapter.get_latest_version()
        current_version = current_record.version

        # 比较版本
        has_update = self._compare_versions(latest_version, current_version) > 0

        return UpdateInfo(
            name=name,
            current_version=current_version,
            latest_version=latest_version,
            has_update=has_update,
            download_size=adapter.get_download_size(latest_version) if has_update else 0,
        )

    def check_updates(self, names: Optional[List[str]] = None) -> List[UpdateInfo]:
        """检查多个数据库的更新

        Args:
            names: 数据库名称列表，如果为None则检查所有已安装数据库

        Returns:
            更新信息列表
        """
        if names is None:
            # 检查所有已安装数据库
            installed = self._state_manager.get_installed_databases()
            names = [r.name for r in installed]

        updates = []
        for name in names:
            update_info = self.check_update(name)
            if update_info and update_info.has_update:
                updates.append(update_info)

        return updates

    def update(
        self,
        name: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """更新单个数据库

        Args:
            name: 数据库名称
            options: 更新选项
                - keep_old: 是否保留旧版本
                - force: 是否强制更新

        Returns:
            如果更新成功返回True，否则返回False
        """
        options = options or {}
        keep_old = options.get("keep_old", False)
        force = options.get("force", False)

        # 检查是否有更新
        update_info = self.check_update(name)
        if not update_info:
            self._logger.warning(f"无法检查更新: {name}")
            return False

        if not update_info.has_update and not force:
            self._logger.info(f"{name} 已经是最新版本")
            return True

        # 获取适配器
        adapter = self._registry.get(name)
        if not adapter:
            self._logger.error(f"未找到适配器: {name}")
            return False

        # 获取当前安装记录
        current_record = self._state_manager.get_database_info(name)
        if not current_record:
            self._logger.error(f"未找到当前安装记录: {name}")
            return False

        self._logger.info(
            f"更新 {name}: {update_info.current_version} -> {update_info.latest_version}"
        )

        try:
            # 设置新的安装状态
            current_record.status = InstallationStatus.UPDATING
            current_record.last_updated = datetime.now()
            self._state_manager.save_record(current_record)

            # 备份旧版本（如果需要）
            if keep_old:
                old_path = current_record.install_path
                backup_path = Path(str(old_path) + f".backup.{update_info.current_version}")
                FileSystem.safe_copy(old_path, backup_path)
                self._logger.info(f"备份旧版本到: {backup_path}")

            # 下载新版本
            temp_path = Path(f"/tmp/biodeploy/{name}_{update_info.latest_version}")
            temp_path.parent.mkdir(parents=True, exist_ok=True)

            if not adapter.download(
                update_info.latest_version,
                temp_path,
                options,
            ):
                self._logger.error("下载新版本失败")
                current_record.status = InstallationStatus.FAILED
                current_record.error_message = "Download failed"
                self._state_manager.save_record(current_record)
                return False

            # 安装新版本
            install_path = current_record.install_path
            if not keep_old:
                # 如果不保留旧版本，先删除
                FileSystem.safe_remove(install_path)

            if not adapter.install(temp_path, install_path, options):
                self._logger.error("安装新版本失败")
                current_record.status = InstallationStatus.FAILED
                current_record.error_message = "Installation failed"
                self._state_manager.save_record(current_record)
                return False

            # 验证安装
            if not adapter.verify(install_path):
                self._logger.error("验证安装失败")
                current_record.status = InstallationStatus.FAILED
                current_record.error_message = "Verification failed"
                self._state_manager.save_record(current_record)
                return False

            # 更新记录
            current_record.version = update_info.latest_version
            current_record.status = InstallationStatus.COMPLETED
            current_record.install_time = datetime.now()
            current_record.error_message = None
            self._state_manager.save_record(current_record)

            # 清理临时文件
            FileSystem.safe_remove(temp_path)

            self._logger.info(f"更新成功: {name} {update_info.latest_version}")
            return True

        except Exception as e:
            self._logger.error(f"更新失败: {e}")
            if current_record:
                current_record.status = InstallationStatus.FAILED
                current_record.error_message = str(e)
                self._state_manager.save_record(current_record)
            return False

    def update_all(
        self,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """更新所有可更新的数据库

        Args:
            options: 更新选项

        Returns:
            数据库名称到更新结果的映射
        """
        updates = self.check_updates()
        results = {}

        for update_info in updates:
            results[update_info.name] = self.update(update_info.name, options)

        return results

    def rollback(self, name: str, target_version: str) -> bool:
        """回滚到指定版本

        Args:
            name: 数据库名称
            target_version: 目标版本

        Returns:
            如果回滚成功返回True，否则返回False
        """
        # 检查目标版本是否存在（通过备份）
        current_record = self._state_manager.get_database_info(name)
        if not current_record:
            self._logger.error(f"未找到当前安装: {name}")
            return False

        backup_path = Path(f"{current_record.install_path}.backup.{target_version}")
        if not backup_path.exists():
            self._logger.error(f"未找到备份版本: {target_version}")
            return False

        try:
            # 恢复备份
            FileSystem.safe_remove(current_record.install_path)
            FileSystem.safe_move(backup_path, current_record.install_path)

            # 更新状态
            current_record.version = target_version
            current_record.status = InstallationStatus.COMPLETED
            current_record.last_updated = datetime.now()
            self._state_manager.save_record(current_record)

            self._logger.info(f"回滚成功: {name} -> {target_version}")
            return True

        except Exception as e:
            self._logger.error(f"回滚失败: {e}")
            return False

    def _compare_versions(self, version1: str, version2: str) -> int:
        """比较两个版本号

        Args:
            version1: 版本1
            version2: 版本2

        Returns:
            如果version1 > version2返回1，相等返回0，小于返回-1
        """
        try:
            v1_parts = [int(x) for x in version1.split(".")]
            v2_parts = [int(x) for x in version2.split(".")]

            for i in range(max(len(v1_parts), len(v2_parts))):
                v1 = v1_parts[i] if i < len(v1_parts) else 0
                v2 = v2_parts[i] if i < len(v2_parts) else 0

                if v1 > v2:
                    return 1
                elif v1 < v2:
                    return -1

            return 0
        except ValueError:
            # 无法解析为数字，按字符串比较
            if version1 > version2:
                return 1
            elif version1 < version2:
                return -1
            return 0

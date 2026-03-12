"""
适配器基类

定义数据库适配器的统一接口。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from biodeploy.models.metadata import DatabaseMetadata
from biodeploy.models.state import InstallationRecord


class BaseAdapter(ABC):
    """适配器基类

    所有数据库适配器都必须实现这个接口。

    Attributes:
        database_name: 数据库名称
    """

    @property
    @abstractmethod
    def database_name(self) -> str:
        """数据库名称

        Returns:
            数据库名称（唯一标识）
        """
        pass

    @abstractmethod
    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        """获取数据库元数据

        Args:
            version: 数据库版本，如果为None则返回最新版本

        Returns:
            数据库元数据
        """
        pass

    @abstractmethod
    def get_available_versions(self) -> List[str]:
        """获取可用版本列表

        Returns:
            版本列表
        """
        pass

    @abstractmethod
    def download(
        self,
        version: str,
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """下载数据库

        Args:
            version: 数据库版本
            target_path: 目标路径
            options: 下载选项

        Returns:
            如果成功返回True，否则返回False
        """
        pass

    @abstractmethod
    def install(
        self,
        source_path: Path,
        install_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """安装数据库

        Args:
            source_path: 源路径（下载的文件）
            install_path: 安装路径
            options: 安装选项

        Returns:
            如果成功返回True，否则返回False
        """
        pass

    @abstractmethod
    def verify(self, install_path: Path) -> bool:
        """验证安装完整性

        Args:
            install_path: 安装路径

        Returns:
            如果安装完整返回True，否则返回False
        """
        pass

    @abstractmethod
    def uninstall(self, install_path: Path) -> bool:
        """卸载数据库

        Args:
            install_path: 安装路径

        Returns:
            如果成功返回True，否则返回False
        """
        pass

    def get_latest_version(self) -> str:
        """获取最新版本

        Returns:
            最新版本号
        """
        versions = self.get_available_versions()
        if not versions:
            raise ValueError(f"没有可用的版本: {self.database_name}")
        return max(versions)

    def is_version_available(self, version: str) -> bool:
        """检查版本是否可用

        Args:
            version: 版本号

        Returns:
            如果版本可用返回True，否则返回False
        """
        return version in self.get_available_versions()

    def get_installation_size(self, version: str) -> int:
        """获取安装大小

        Args:
            version: 版本号

        Returns:
            安装大小（字节）
        """
        metadata = self.get_metadata(version)
        return metadata.size

    def get_dependencies(self, version: str) -> List[str]:
        """获取依赖

        Args:
            version: 版本号

        Returns:
            依赖列表
        """
        metadata = self.get_metadata(version)
        return metadata.dependencies

    def get_environment_variables(
        self, install_path: Path, version: str
    ) -> Dict[str, str]:
        """获取环境变量

        Args:
            install_path: 安装路径
            version: 版本号

        Returns:
            环境变量字典
        """
        metadata = self.get_metadata(version)

        # 基本环境变量
        env_vars = {
            f"{self.database_name.upper()}_DB_PATH": str(install_path),
            f"{self.database_name.upper()}_VERSION": version,
        }

        # 添加数据库特定的环境变量
        if metadata.index_types:
            for index_type in metadata.index_types:
                index_path = install_path / "indexes" / index_type
                env_vars[f"{self.database_name.upper()}_{index_type.upper()}_INDEX"] = str(
                    index_path
                )

        return env_vars

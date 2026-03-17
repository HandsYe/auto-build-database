"""
KEGG 数据库适配器

支持 KEGG 数据库的下载和安装。
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from biodeploy.adapters.adapter_registry import register_adapter
from biodeploy.adapters.base_adapter import BaseAdapter
from biodeploy.models.metadata import DatabaseMetadata, DownloadSource
from biodeploy.models.errors import DatabaseError, ErrorCode
from biodeploy.services.download_service import DownloadService
from biodeploy.infrastructure.filesystem import FileSystem
from biodeploy.infrastructure.logger import get_logger


@register_adapter
class KEGGAdapter(BaseAdapter):
    """KEGG 数据库适配器

    支持 KEGG 通路数据库的下载和安装。
    """

    BASE_URL = "https://www.kegg.jp/kegg/"
    
    DATABASE_TYPES = {
        "genes": {
            "name": "KEGG GENES",
            "description": "KEGG GENES database",
            "files": ["genes/genes.tar.gz"],
        },
        "genome": {
            "name": "KEGG GENOME",
            "description": "KEGG GENOME database",
            "files": ["genome/genome.tar.gz"],
        },
        "pathway": {
            "name": "KEGG PATHWAY",
            "description": "KEGG PATHWAY database",
            "files": ["pathway/pathway.tar.gz"],
        },
        "reaction": {
            "name": "KEGG REACTION",
            "description": "KEGG REACTION database",
            "files": ["reaction/reaction.tar.gz"],
        },
        "compound": {
            "name": "KEGG COMPOUND",
            "description": "KEGG COMPOUND database",
            "files": ["compound/compound.tar.gz"],
        },
        "full": {
            "name": "KEGG Full",
            "description": "Complete KEGG database",
            "files": [
                "genes/genes.tar.gz",
                "genome/genome.tar.gz",
                "pathway/pathway.tar.gz",
                "reaction/reaction.tar.gz",
                "compound/compound.tar.gz",
            ],
        },
    }

    def __init__(self, db_type: str = "full") -> None:
        """初始化 KEGG 适配器

        Args:
            db_type: 数据库类型 (genes, genome, pathway, reaction, compound, full)
        """
        if db_type not in self.DATABASE_TYPES:
            raise ValueError(f"不支持的数据库类型：{db_type}")

        self.db_type = db_type
        self.db_info = self.DATABASE_TYPES[db_type]
        self.logger = get_logger(f"kegg_adapter.{db_type}")
        self.download_service = DownloadService()

    @property
    def database_name(self) -> str:
        """数据库名称"""
        return f"kegg_{self.db_type}"

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        """获取数据库元数据

        Args:
            version: 版本号

        Returns:
            数据库元数据
        """
        if version is None:
            version = self.get_latest_version()

        # 构建下载源
        sources = []
        for file_pattern in self.db_info["files"]:
            url = f"{self.BASE_URL}{file_pattern}"
            sources.append(
                DownloadSource(
                    url=url,
                    protocol="https",
                    priority=1,
                    is_mirror=False,
                )
            )

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.db_info["name"],
            description=self.db_info["description"],
            size=10 * 1024 * 1024 * 1024,  # 10GB (估计值)
            file_count=len(self.db_info["files"]),
            formats=["tar.gz", "kgml"],
            download_sources=sources,
            checksums={},
            dependencies=["wget"],
            license="Academic",
            website="https://www.kegg.jp/",
            tags=["kegg", "pathway", "metabolism"],
            category="pathway",
            last_updated=datetime.now(),
        )

    def get_available_versions(self) -> List[str]:
        """获取可用版本列表

        Returns:
            版本列表
        """
        return ["latest"]

    def get_latest_version(self) -> str:
        """获取最新版本

        Returns:
            最新版本号
        """
        return "latest"

    def download(
        self,
        version: str,
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """下载数据库

        Args:
            version: 版本号
            target_path: 目标路径
            options: 下载选项
            progress_callback: 进度回调函数

        Returns:
            如果成功返回 True
        """
        target_path = Path(target_path)
        options = options or {}

        self.logger.info(f"开始下载 {self.database_name} {version}")

        metadata = self.get_metadata(version)

        # 下载所有文件
        for i, source in enumerate(metadata.download_sources):
            file_name = source.url.split("/")[-1]
            file_path = target_path / file_name

            self.logger.info(f"下载文件 {i+1}/{len(metadata.download_sources)}: {file_name}")

            result = self.download_service.download(
                sources=[source],
                target_path=file_path,
                options=options,
                progress_callback=progress_callback,
            )

            if not result.success:
                raise DatabaseError(
                    f"下载失败：{file_name}",
                    ErrorCode.DOWNLOAD_FAILED,
                    {"database": self.database_name, "file": file_name},
                )

        self.logger.info(f"下载完成：{target_path}")
        return True

    def install(
        self,
        source_path: Path,
        install_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """安装数据库

        Args:
            source_path: 源路径
            install_path: 安装路径
            options: 安装选项

        Returns:
            如果成功返回 True
        """
        source_path = Path(source_path)
        install_path = Path(install_path)
        options = options or {}

        self.logger.info(f"开始安装 {self.database_name}")

        try:
            FileSystem.ensure_directory(install_path)

            # 解压 tar.gz 文件
            import tarfile
            for tar_file in source_path.glob("*.tar.gz"):
                self.logger.info(f"解压：{tar_file}")
                with tarfile.open(tar_file, "r:gz") as tar:
                    tar.extractall(path=install_path)

            # 验证安装
            if not self.verify(install_path):
                raise DatabaseError(
                    "安装验证失败",
                    ErrorCode.INSTALL_FAILED,
                    {"path": str(install_path)},
                )

            self.logger.info(f"安装完成：{install_path}")
            return True

        except Exception as e:
            self.logger.error(f"安装失败：{e}")
            return False

    def verify(self, install_path: Path) -> bool:
        """验证安装完整性

        Args:
            install_path: 安装路径

        Returns:
            如果安装完整返回 True
        """
        install_path = Path(install_path)

        if not install_path.exists():
            return False

        # 检查是否有数据文件
        files = list(install_path.rglob("*"))
        return len(files) > 0

    def uninstall(self, install_path: Path) -> bool:
        """卸载数据库

        Args:
            install_path: 安装路径

        Returns:
            如果成功返回 True
        """
        install_path = Path(install_path)

        if not install_path.exists():
            self.logger.warning(f"安装路径不存在：{install_path}")
            return True

        try:
            FileSystem.safe_remove(install_path)
            self.logger.info(f"卸载完成：{install_path}")
            return True
        except Exception as e:
            self.logger.error(f"卸载失败：{e}")
            return False

    def get_download_size(self, version: Optional[str] = None) -> int:
        """获取下载大小

        Args:
            version: 版本号

        Returns:
            下载大小（字节）
        """
        return 10 * 1024 * 1024 * 1024  # 10GB

    def get_dependencies(self, version: Optional[str] = None) -> List[str]:
        """获取依赖工具列表

        Args:
            version: 版本号

        Returns:
            依赖列表
        """
        return ["wget", "tar"]

    def get_system_requirements(self, version: Optional[str] = None) -> Dict[str, Any]:
        """获取系统要求

        Args:
            version: 版本号

        Returns:
            系统要求字典
        """
        return {
            "min_disk_space": 20 * 1024 * 1024 * 1024,  # 20GB
            "min_memory": 8 * 1024 * 1024 * 1024,  # 8GB
            "required_tools": ["wget", "tar"],
        }

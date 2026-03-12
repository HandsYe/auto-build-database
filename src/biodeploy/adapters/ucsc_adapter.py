"""
UCSC适配器

支持UCSC数据库（Genome Browser、Table Browser）的下载和安装。
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from biodeploy.adapters.adapter_registry import register_adapter
from biodeploy.adapters.base_adapter import BaseAdapter
from biodeploy.infrastructure.filesystem import FileSystem
from biodeploy.infrastructure.logger import logger
from biodeploy.models.metadata import DatabaseMetadata, DownloadSource
from biodeploy.services.download_service import DownloadService


@register_adapter
class UCSCAdapter(BaseAdapter):
    """UCSC数据库适配器"""

    BASE_URL = "https://hgdownload.soe.ucsc.edu/"
    GOLDEN_PATH = "goldenPath/"

    DATABASES = {
        "genome": {
            "display_name": "UCSC Genome Browser",
            "description": "UCSC Genome Browser Data",
            "paths": ["goldenPath/{genome}/bigZips/"],
        },
        "tables": {
            "display_name": "UCSC Table Browser",
            "description": "UCSC Table Browser Data",
            "paths": ["goldenPath/{genome}/database/"],
        },
    }

    def __init__(self, db_name: str = "genome", genome: str = "hg38"):
        """初始化UCSC适配器

        Args:
            db_name: 数据库名称 (genome, tables)
            genome: 基因组版本 (hg38, hg19, mm39, mm10, etc.)
        """
        self.db_name = db_name
        self.genome = genome
        self._logger = logger.get_logger("ucsc_adapter")
        self._download_service = DownloadService()

    @property
    def database_name(self) -> str:
        """数据库名称"""
        return f"ucsc_{self.db_name}_{self.genome}"

    @property
    def display_name(self) -> str:
        """显示名称"""
        db_info = self.DATABASES.get(self.db_name, {})
        return f"{db_info.get('display_name', 'UCSC')} ({self.genome})"

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        """获取数据库元数据"""
        db_info = self.DATABASES.get(self.db_name, {})

        # 构建URL
        paths = db_info.get("paths", [])
        urls = [
            self.BASE_URL + path.format(genome=self.genome)
            for path in paths
        ]

        sources = [
            DownloadSource(
                url=url,
                protocol="https",
                priority=1,
                is_mirror=False,
            )
            for url in urls
        ]

        return DatabaseMetadata(
            name=self.database_name,
            version=version or self.get_latest_version(),
            display_name=self.display_name,
            description=db_info.get("description", ""),
            size=0,
            file_count=0,
            formats=["fasta", "2bit", "txt", "sql"],
            download_sources=sources,
            checksums={},
            dependencies=["wget", "twoBitToFa"],
            license="UCSC License",
            website="https://genome.ucsc.edu/",
        )

    def get_available_versions(self) -> List[str]:
        """获取可用版本列表"""
        return ["latest"]

    def get_latest_version(self) -> str:
        """获取最新版本"""
        return "latest"

    def download(
        self,
        version: str,
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None,
    ) -> bool:
        """下载数据库"""
        options = options or {}
        self._logger.info(f"开始下载 {self.database_name} 版本 {version}")

        metadata = self.get_metadata(version)

        result = self._download_service.download(
            sources=metadata.download_sources,
            target_path=target_path,
            resume=True,
            progress_callback=progress_callback,
            proxy=options.get("proxy"),
        )

        return result.success

    def install(
        self,
        source_path: Path,
        install_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """安装数据库"""
        options = options or {}
        self._logger.info(f"开始安装 {self.database_name} 到 {install_path}")

        try:
            FileSystem.ensure_directory(install_path)

            if source_path.is_dir():
                FileSystem.safe_copy(source_path, install_path, overwrite=True)
            else:
                FileSystem.ensure_parent_directory(install_path)
                FileSystem.safe_copy(source_path, install_path, overwrite=True)

            self._logger.info(f"安装完成: {install_path}")
            return True

        except Exception as e:
            self._logger.error(f"安装失败: {e}")
            return False

    def verify(self, install_path: Path) -> bool:
        """验证安装完整性"""
        if not install_path.exists():
            return False

        # 检查是否有必要文件
        twobit_files = list(install_path.rglob("*.2bit"))
        fasta_files = list(install_path.rglob("*.fa"))
        fasta_files.extend(install_path.rglob("*.fasta"))

        return len(twobit_files) > 0 or len(fasta_files) > 0

    def uninstall(self, install_path: Path) -> bool:
        """卸载数据库"""
        self._logger.info(f"卸载 {self.database_name}: {install_path}")
        return FileSystem.safe_remove(install_path)

    def get_download_size(self, version: str) -> int:
        """获取下载大小"""
        return 0

    def get_dependencies(self) -> List[str]:
        """获取依赖工具列表"""
        return ["wget", "gzip"]

    def get_system_requirements(self) -> Dict[str, Any]:
        """获取系统要求"""
        return {
            "min_disk_space": 5 * 1024 * 1024 * 1024,  # 5GB
            "min_memory": 2 * 1024 * 1024 * 1024,  # 2GB
            "required_tools": ["wget"],
        }

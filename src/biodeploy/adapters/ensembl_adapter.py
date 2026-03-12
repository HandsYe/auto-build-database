"""
Ensembl适配器

支持Ensembl数据库（Genomes、Variation、Regulation）的下载和安装。
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from biodeploy.adapters.adapter_registry import register_adapter
from biodeploy.adapters.base_adapter import BaseAdapter
from biodeploy.infrastructure.filesystem import FileSystem
from biodeploy.infrastructure.logger import get_logger
from biodeploy.models.metadata import DatabaseMetadata, DownloadSource
from biodeploy.services.download_service import DownloadService


@register_adapter
class EnsemblAdapter(BaseAdapter):
    """Ensembl数据库适配器"""

    BASE_URL = "https://ftp.ensembl.org/pub/"
    MIRRORS = {
        "us": "https://uswest.ensembl.org/pub/",
        "asia": "https://asia.ensembl.org/pub/",
    }

    DATABASE_TYPES = {
        "genomes": {
            "display_name": "Ensembl Genomes",
            "description": "Ensembl Genome Assemblies",
        },
        "variation": {
            "display_name": "Ensembl Variation",
            "description": "Ensembl Variation Data",
        },
        "regulation": {
            "display_name": "Ensembl Regulation",
            "description": "Ensembl Regulation Data",
        },
    }

    def __init__(self, db_type: str = "genomes"):
        """初始化Ensembl适配器

        Args:
            db_type: 数据库类型 (genomes, variation, regulation)
        """
        self.db_type = db_type
        self._logger = get_logger("ensembl_adapter")
        self._download_service = DownloadService()

    @property
    def database_name(self) -> str:
        """数据库名称"""
        return f"ensembl_{self.db_type}"

    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.DATABASE_TYPES.get(self.db_type, {}).get(
            "display_name", f"Ensembl {self.db_type}"
        )

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        """获取数据库元数据"""
        db_info = self.DATABASE_TYPES.get(self.db_type, {})

        # 构建下载源
        sources = [
            DownloadSource(
                url=self.BASE_URL,
                protocol="https",
                priority=1,
                is_mirror=False,
            )
        ]

        # 添加镜像源
        for region, url in self.MIRRORS.items():
            sources.append(
                DownloadSource(
                    url=url,
                    protocol="https",
                    priority=2,
                    is_mirror=True,
                    region=region,
                )
            )

        return DatabaseMetadata(
            name=self.database_name,
            version=version or self.get_latest_version(),
            display_name=self.display_name,
            description=db_info.get("description", ""),
            size=0,
            file_count=0,
            formats=["fasta", "gff3", "gtf", "vcf", "emf"],
            download_sources=sources,
            checksums={},
            dependencies=["wget", "gtf_to_gff3"],
            license="Apache-2.0",
            website="https://www.ensembl.org/",
        )

    def get_available_versions(self) -> List[str]:
        """获取可用版本列表"""
        # Ensembl使用发布版本号
        return ["112", "111", "110", "109", "108"]

    def get_latest_version(self) -> str:
        """获取最新版本"""
        return "112"

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

        # 检查是否有必要的文件
        fasta_files = list(install_path.rglob("*.fa"))
        fasta_files.extend(install_path.rglob("*.fasta"))
        gff_files = list(install_path.rglob("*.gff3"))
        gtf_files = list(install_path.rglob("*.gtf"))

        return len(fasta_files) > 0 or len(gff_files) > 0 or len(gtf_files) > 0

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

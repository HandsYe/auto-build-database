"""
NCBI数据库适配器

实现NCBI数据库的下载和安装。
"""

import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from biodeploy.adapters.adapter_registry import register_adapter
from biodeploy.adapters.base_adapter import BaseAdapter
from biodeploy.models.metadata import DatabaseMetadata, DownloadSource
from biodeploy.models.errors import DatabaseError, ErrorCode
from biodeploy.services.download_service import DownloadService
from biodeploy.services.checksum_service import ChecksumService
from biodeploy.infrastructure.logger import get_logger


@register_adapter
class NCBIAdapter(BaseAdapter):
    """NCBI数据库适配器

    支持NCBI的RefSeq、GenBank、dbSNP等数据库。
    """

    # NCBI FTP 基础 URL
    BASE_URL = "https://ftp.ncbi.nlm.nih.gov"
    MIRROR_URL = "https://mirrors.ustc.edu.cn/ncbi"

    # NCBI数据库类型
    # 版本号为纯数字，如 1445, 1446
    DATABASE_TYPES = {
        "refseq_protein": {
            "name": "NCBI RefSeq Protein",
            "description": "NCBI Reference Sequence Protein Database",
            "path": "refseq/release/complete",
            "file_pattern": "complete.{version}.protein.faa.gz",
            "version_range": range(1441, 1460),  # 支持的版本范围
        },
        "refseq_genomic": {
            "name": "NCBI RefSeq Genomic",
            "description": "NCBI Reference Sequence Genomic Database (first part)",
            "path": "refseq/release/complete",
            "file_pattern": "complete.{version}.1.genomic.fna.gz",
            "version_range": range(1441, 1460),
        },
        "refseq_wp_protein": {
            "name": "NCBI RefSeq WP Protein",
            "description": "NCBI Reference Sequence Whole Proteome Protein Database",
            "path": "refseq/release/complete",
            "file_pattern": "complete.wp_protein.{version}.protein.faa.gz",
            "version_range": range(1, 150),
        },
        "genbank": {
            "name": "NCBI GenBank",
            "description": "NCBI GenBank Sequence Database (divided by organism groups)",
            "path": "genbank",
            # GenBank 使用分段文件格式：gb{division}{number}.seq.gz
            "divisions": ["bct", "inv", "mam", "phg", "pln", "pri", "rod", "vrl", "vrt"],
            "file_range": range(1, 200),
        },
    }

    def __init__(self, db_type: str = "refseq_protein") -> None:
        """初始化NCBI适配器

        Args:
            db_type: 数据库类型
        """
        if db_type not in self.DATABASE_TYPES:
            raise ValueError(f"不支持的数据库类型: {db_type}")

        self.db_type = db_type
        self.db_info = self.DATABASE_TYPES[db_type]
        self.logger = get_logger(f"ncbi_adapter.{db_type}")

        # 初始化服务
        self.download_service = DownloadService()
        self.checksum_service = ChecksumService()

    @property
    def database_name(self) -> str:
        """数据库名称"""
        return f"ncbi_{self.db_type}"

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        """获取数据库元数据

        Args:
            version: 版本号，RefSeq使用纯数字（如1445）

        Returns:
            数据库元数据
        """
        if version is None:
            version = self.get_latest_version()

        sources = []
        file_count = 1

        if self.db_type == "genbank":
            # GenBank 使用多个分部文件
            divisions = self.db_info.get("divisions", ["bct"])
            file_range = self.db_info.get("file_range", range(1, 200))

            for division in divisions:
                for num in file_range:
                    file_name = f"gb{division}{num}.seq.gz"
                    # 主站点
                    sources.append(
                        DownloadSource(
                            url=f"{self.BASE_URL}/{self.db_info['path']}/{file_name}",
                            protocol="https",
                            priority=1,
                            is_mirror=False,
                            region="US",
                        )
                    )
                    # 镜像站点
                    sources.append(
                        DownloadSource(
                            url=f"{self.MIRROR_URL}/{self.db_info['path']}/{file_name}",
                            protocol="https",
                            priority=2,
                            is_mirror=True,
                            region="CN",
                        )
                    )
            file_count = len(divisions) * len(list(file_range)) * 2
        else:
            # RefSeq 使用单一文件
            file_pattern = self.db_info.get("file_pattern", "")
            file_name = file_pattern.format(version=version)
            path = self.db_info.get("path", "")

            # 主站点
            sources.append(
                DownloadSource(
                    url=f"{self.BASE_URL}/{path}/{file_name}",
                    protocol="https",
                    priority=1,
                    is_mirror=False,
                    region="US",
                )
            )
            # 镜像站点
            sources.append(
                DownloadSource(
                    url=f"{self.MIRROR_URL}/{path}/{file_name}",
                    protocol="https",
                    priority=2,
                    is_mirror=True,
                    region="CN",
                )
            )
            file_count = 2

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.db_info["name"],
            description=self.db_info["description"],
            size=1024 * 1024 * 1024 * 5,  # 5GB (估计值)
            file_count=file_count,
            formats=["fasta", "genbank"],
            download_sources=sources,
            checksums={},
            dependencies=["wget", "gunzip"],
            license="Public Domain",
            website="https://www.ncbi.nlm.nih.gov/",
            tags=["ncbi", "reference", self.db_type],
            category="sequence",
            last_updated=datetime.now(),
        )

    def get_available_versions(self) -> List[str]:
        """获取可用版本列表

        Returns:
            版本列表
        """
        if self.db_type == "genbank":
            # GenBank 没有版本号概念
            return ["latest"]

        version_range = self.db_info.get("version_range", range(1441, 1450))
        return [str(v) for v in sorted(version_range, reverse=True)]

    def get_latest_version(self) -> str:
        """获取最新版本

        Returns:
            最新版本号
        """
        if self.db_type == "genbank":
            return "latest"

        versions = self.get_available_versions()
        return versions[0] if versions else "1445"

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
            如果成功返回True
        """
        target_path = Path(target_path)
        options = options or {}

        self.logger.info(f"开始下载 {self.database_name} {version}")

        # 获取元数据
        metadata = self.get_metadata(version)

        # 下载文件
        result = self.download_service.download(
            sources=metadata.download_sources,
            target_path=target_path / f"{self.database_name}_{version}.gz",
            options=options,
            progress_callback=progress_callback,
        )

        if not result.success:
            raise DatabaseError(
                f"下载失败: {result.error_message}",
                ErrorCode.DOWNLOAD_FAILED,
                {"database": self.database_name, "version": version},
            )

        self.logger.info(f"下载完成: {result.file_path}")
        return True

    def install(
        self,
        source_path: Path,
        install_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """安装数据库

        Args:
            source_path: 源路径（下载的.gz文件）
            install_path: 安装路径
            options: 安装选项

        Returns:
            如果成功返回True
        """
        source_path = Path(source_path)
        install_path = Path(install_path)
        options = options or {}

        self.logger.info(f"开始安装 {self.database_name}")

        # 确保安装目录存在
        install_path.mkdir(parents=True, exist_ok=True)

        # 兼容：source_path 可能是“下载目录”，里面包含 .gz 文件
        if source_path.is_dir():
            gz_files = sorted(source_path.glob("*.gz"))
            if not gz_files:
                raise DatabaseError(
                    "未找到可安装的 .gz 文件",
                    ErrorCode.INSTALL_FAILED,
                    {"path": str(source_path)},
                )
            source_path = gz_files[0]

        # 解压文件
        if source_path.suffix == ".gz":
            self.logger.info(f"解压文件: {source_path}")

            output_file = install_path / source_path.stem

            with gzip.open(source_path, "rb") as f_in:
                with open(output_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            self.logger.info(f"解压完成: {output_file}")

        # 验证安装
        if not self.verify(install_path):
            raise DatabaseError(
                "安装验证失败",
                ErrorCode.INSTALL_FAILED,
                {"path": str(install_path)},
            )

        self.logger.info(f"安装完成: {install_path}")
        return True

    def verify(self, install_path: Path) -> bool:
        """验证安装完整性

        Args:
            install_path: 安装路径

        Returns:
            如果安装完整返回True
        """
        install_path = Path(install_path)

        if not install_path.exists():
            return False

        # 检查是否有FASTA文件
        fasta_files = (
            list(install_path.glob("*.fa"))
            + list(install_path.glob("*.fasta"))
            + list(install_path.glob("*.faa"))
            + list(install_path.glob("*.fna"))
        )

        if not fasta_files:
            self.logger.warning(f"未找到FASTA文件: {install_path}")
            return False

        # 检查文件大小
        for fasta_file in fasta_files:
            if fasta_file.stat().st_size == 0:
                self.logger.warning(f"文件为空: {fasta_file}")
                return False

        self.logger.info(f"安装验证通过: {install_path}")
        return True

    def uninstall(self, install_path: Path) -> bool:
        """卸载数据库

        Args:
            install_path: 安装路径

        Returns:
            如果成功返回True
        """
        install_path = Path(install_path)

        if not install_path.exists():
            self.logger.warning(f"安装路径不存在: {install_path}")
            return True

        try:
            shutil.rmtree(install_path)
            self.logger.info(f"卸载完成: {install_path}")
            return True
        except Exception as e:
            self.logger.error(f"卸载失败: {e}")
            return False

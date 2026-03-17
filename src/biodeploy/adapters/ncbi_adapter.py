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

    # NCBI数据库类型
    DATABASE_TYPES = {
        "refseq_protein": {
            "name": "NCBI RefSeq Protein",
            "description": "NCBI Reference Sequence Protein Database",
            "url_pattern": "https://ftp.ncbi.nlm.nih.gov/refseq/release/complete/complete.{version}.protein.faa.gz",
        },
        "refseq_genomic": {
            "name": "NCBI RefSeq Genomic",
            "description": "NCBI Reference Sequence Genomic Database",
            "url_pattern": "https://ftp.ncbi.nlm.nih.gov/refseq/release/complete/complete.{version}.genomic.fna.gz",
        },
        "genbank": {
            "name": "NCBI GenBank",
            "description": "NCBI GenBank Sequence Database",
            "url_pattern": "https://ftp.ncbi.nlm.nih.gov/genbank/gb{version}.seq.gz",
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
            version: 版本号，格式为YYYY.MM

        Returns:
            数据库元数据
        """
        if version is None:
            version = self.get_latest_version()

        # 创建下载源
        primary_source = DownloadSource(
            url=self.db_info["url_pattern"].format(version=version.replace(".", "")),
            protocol="https",
            priority=1,
            is_mirror=False,
            region="US",
        )

        # 中国镜像
        mirror_source = DownloadSource(
            url=self.db_info["url_pattern"]
            .format(version=version.replace(".", ""))
            .replace("ftp.ncbi.nlm.nih.gov", "mirrors.ustc.edu.cn/ncbi"),
            protocol="https",
            priority=2,
            is_mirror=True,
            region="CN",
        )

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.db_info["name"],
            description=self.db_info["description"],
            size=1024 * 1024 * 1024 * 5,  # 5GB (估计值)
            file_count=1,
            formats=["fasta"],
            download_sources=[primary_source, mirror_source],
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
        return ["1445", "1444", "1443", "1442", "1441"]

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

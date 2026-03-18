"""
UCSC适配器

支持UCSC数据库（Genome Browser、Table Browser）的下载和安装。
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
class UCSCAdapter(BaseAdapter):
    """UCSC数据库适配器

    支持 UCSC Genome Browser 的基因组数据和注释下载。
    """

    BASE_URL = "https://hgdownload.soe.ucsc.edu"

    # 常用基因组版本
    COMMON_GENOMES = {
        "hg38": {"name": "Human (GRCh38)", "assembly": "GRCh38"},
        "hg19": {"name": "Human (GRCh37/hg19)", "assembly": "GRCh37"},
        "mm39": {"name": "Mouse (GRCm39)", "assembly": "GRCm39"},
        "mm10": {"name": "Mouse (GRCm38/mm10)", "assembly": "GRCm38"},
        "rn7": {"name": "Rat (mRatBN7.2)", "assembly": "mRatBN7.2"},
        "rn6": {"name": "Rat (Rnor_6.0)", "assembly": "Rnor_6.0"},
        "dm6": {"name": "Fruit Fly (BDGP Release 6)", "assembly": "BDGP6"},
        "ce11": {"name": "C. elegans (WBcel235)", "assembly": "WBcel235"},
        "sacCer3": {"name": "Yeast (S288C)", "assembly": "R64"},
    }

    # 数据库类型定义
    DATABASE_TYPES = {
        "genome": {
            "display_name": "UCSC Genome Sequence",
            "description": "Reference genome sequence in FASTA format",
            "path": "goldenPath/{genome}/bigZips/",
            "files": {
                "2bit": "{genome}.2bit",
                "fasta": "{genome}.fa.gz",
                "chrom_fasta": "{genome}.chromFa.tar.gz",
                "masked_fasta": "{genome}.fa.masked.gz",
            },
        },
        "genes": {
            "display_name": "UCSC Gene Annotations",
            "description": "Gene annotations in various formats",
            "path": "goldenPath/{genome}/database/",
            "files": {
                "refgene": "refGene.txt.gz",
                "knowngene": "knownGene.txt.gz",
                "ensgene": "ensGene.txt.gz",
                "ccds": "ccdsGene.txt.gz",
            },
        },
        "alignment": {
            "display_name": "UCSC Alignments",
            "description": "Sequence alignment data",
            "path": "goldenPath/{genome}/bigZips/",
            "files": {
                "alignment": "{genome}.fa.align.gz",
            },
        },
    }

    def __init__(self, db_type: str = "genome", genome: str = "hg38", file_type: str = "fasta"):
        """初始化UCSC适配器

        Args:
            db_type: 数据库类型 (genome, genes, alignment)
            genome: 基因组版本 (hg38, hg19, mm39, mm10, etc.)
            file_type: 文件类型 (fasta, 2bit, refgene, etc.)
        """
        if db_type not in self.DATABASE_TYPES:
            raise ValueError(f"不支持的数据库类型: {db_type}")

        self.db_type = db_type
        self.genome = genome
        self.file_type = file_type
        self.db_info = self.DATABASE_TYPES[db_type]
        self._logger = get_logger(f"ucsc_adapter.{db_type}")

    @property
    def database_name(self) -> str:
        """数据库名称"""
        return f"ucsc_{self.db_type}_{self.genome}_{self.file_type}"

    @property
    def display_name(self) -> str:
        """显示名称"""
        db_info = self.db_info
        genome_info = self.COMMON_GENOMES.get(self.genome, {"name": self.genome})
        return f"{db_info.get('display_name', 'UCSC')} - {genome_info['name']}"

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        """获取数据库元数据"""
        # 构建路径
        path_template = self.db_info.get("path", "")
        path = path_template.format(genome=self.genome)

        # 获取文件模板
        files_template = self.db_info.get("files", {})

        # 构建下载源
        sources = []
        for file_key, file_template in files_template.items():
            file_name = file_template.format(genome=self.genome)
            url = f"{self.BASE_URL}/{path}{file_name}"
            sources.append(
                DownloadSource(
                    url=url,
                    protocol="https",
                    priority=1,
                    is_mirror=False,
                    region="US",
                )
            )

        # 确定格式
        formats = []
        if self.db_type == "genome":
            formats = ["2bit", "fasta"]
        elif self.db_type == "genes":
            formats = ["txt", "gtf"]
        elif self.db_type == "alignment":
            formats = ["alignment"]

        return DatabaseMetadata(
            name=self.database_name,
            version=version or self.get_latest_version(),
            display_name=self.display_name,
            description=self.db_info.get("description", ""),
            size=0,
            file_count=len(sources),
            formats=formats,
            download_sources=sources,
            checksums={},
            dependencies=["wget", "twoBitToFa"],
            license="UCSC License",
            website="https://genome.ucsc.edu/",
            tags=["ucsc", self.db_type, self.genome],
            category="sequence" if self.db_type == "genome" else "annotation",
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
        """下载数据库

        Args:
            version: 版本号
            target_path: 目标路径
            options: 下载选项，可包含 'file_type' 指定特定文件类型
            progress_callback: 进度回调函数

        Returns:
            如果成功返回True
        """
        options = options or {}
        self._logger.info(f"开始下载 {self.database_name} 版本 {version}")

        # 允许通过选项覆盖文件类型
        file_type = options.get("file_type", self.file_type)

        metadata = self.get_metadata(version)

        # 如果指定了特定文件类型，只下载该类型的文件
        if file_type and file_type in self.db_info.get("files", {}):
            path = self.db_info["path"].format(genome=self.genome)
            file_name = self.db_info["files"][file_type].format(genome=self.genome)
            specific_url = f"{self.BASE_URL}/{path}{file_name}"

            sources = [
                DownloadSource(
                    url=specific_url,
                    protocol="https",
                    priority=1,
                    is_mirror=False,
                    region="US",
                )
            ]
        else:
            sources = metadata.download_sources

        # 确保目标路径存在
        target_path = Path(target_path)
        target_path.mkdir(parents=True, exist_ok=True)

        result = self._download_service.download(
            sources=sources,
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

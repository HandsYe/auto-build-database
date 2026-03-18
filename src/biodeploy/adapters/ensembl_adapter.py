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
    """Ensembl数据库适配器

    支持 Ensembl 基因组、变异和调控数据的下载。
    """

    BASE_URL = "https://ftp.ensembl.org/pub"
    MIRRORS = {
        "us": "https://uswest.ensembl.org/pub/",
        "asia": "https://asia.ensembl.org/pub/",
    }

    # Ensembl 版本号格式为 release-XXX
    # current_fasta 使用最新版本，current_gtf/gff3 可能滞后一个版本
    CURRENT_VERSION = "115"
    SUPPORTED_VERSIONS = ["115", "114", "113", "112", "111", "110"]

    # 常用物种列表
    COMMON_SPECIES = {
        "homo_sapiens": "Homo sapiens (Human)",
        "mus_musculus": "Mus musculus (Mouse)",
        "rattus_norvegicus": "Rattus norvegicus (Rat)",
        "danio_rerio": "Danio rerio (Zebrafish)",
        "drosophila_melanogaster": "Drosophila melanogaster (Fruit fly)",
        "caenorhabditis_elegans": "Caenorhabditis elegans (Worm)",
        "saccharomyces_cerevisiae": "Saccharomyces cerevisiae (Yeast)",
    }

    # Ensembl 使用 current_* 路径获取最新数据
    DATABASE_TYPES = {
        "genome": {
            "display_name": "Ensembl Genome",
            "description": "Ensembl genome FASTA sequences",
            "path_template": "current_fasta/{species}/dna/",
            "file_pattern": "{species_capitalized}.{assembly}.dna.primary_assembly.fa.gz",
        },
        "cdna": {
            "display_name": "Ensembl cDNA",
            "description": "Ensembl cDNA sequences",
            "path_template": "current_fasta/{species}/cdna/",
            "file_pattern": "{species_capitalized}.{assembly}.cdna.all.fa.gz",
        },
        "ncrna": {
            "display_name": "Ensembl ncRNA",
            "description": "Ensembl non-coding RNA sequences",
            "path_template": "current_fasta/{species}/ncrna/",
            "file_pattern": "{species_capitalized}.{assembly}.ncrna.fa.gz",
        },
        "pep": {
            "display_name": "Ensembl Protein",
            "description": "Ensembl protein sequences",
            "path_template": "current_fasta/{species}/pep/",
            "file_pattern": "{species_capitalized}.{assembly}.pep.all.fa.gz",
        },
        "gtf": {
            "display_name": "Ensembl GTF",
            "description": "Ensembl gene annotation in GTF format",
            "path_template": "current_gtf/{species}/",
            "file_pattern": "{species_capitalized}.{assembly}.{version}.gtf.gz",
        },
        "gff3": {
            "display_name": "Ensembl GFF3",
            "description": "Ensembl gene annotation in GFF3 format",
            "path_template": "current_gff3/{species}/",
            "file_pattern": "{species_capitalized}.{assembly}.{version}.gff3.gz",
        },
        "variation": {
            "display_name": "Ensembl Variation",
            "description": "Ensembl variation data (VCF format)",
            "path_template": "current_variation/vcf/{species}/",
            "file_pattern": "{species_capitalized}_vcf.vcf.gz",
        },
    }

    def __init__(self, db_type: str = "genome", species: str = "homo_sapiens"):
        """初始化Ensembl适配器

        Args:
            db_type: 数据库类型 (genome, cdna, ncrna, pep, gtf, gff3, variation)
            species: 物种名称，如 homo_sapiens, mus_musculus
        """
        if db_type not in self.DATABASE_TYPES:
            raise ValueError(f"不支持的数据库类型: {db_type}")

        self.db_type = db_type
        self.species = species
        self.db_info = self.DATABASE_TYPES[db_type]
        self._logger = get_logger(f"ensembl_adapter.{db_type}")
        self._download_service = DownloadService()

    @property
    def database_name(self) -> str:
        """数据库名称"""
        return f"ensembl_{self.db_type}_{self.species}"

    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.DATABASE_TYPES.get(self.db_type, {}).get(
            "display_name", f"Ensembl {self.db_type}"
        )

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        """获取数据库元数据"""
        version = version or self.get_latest_version()
        db_info = self.DATABASE_TYPES.get(self.db_type, {})

        # 构建路径
        path_template = db_info.get("path_template", "")
        path = path_template.format(version=version, species=self.species)

        # 获取物种显示名称
        species_display = self.COMMON_SPECIES.get(self.species, self.species)

        # 构建具体文件 URL（使用估计的 assembly 名称）
        file_pattern = db_info.get("file_pattern", "")
        # Ensembl 使用 Homo_sapiens 格式（仅首字母大写）
        species_capitalized = self.species[0].upper() + self.species[1:]

        # 获取 assembly 名称（常用物种）
        assembly_map = {
            "homo_sapiens": "GRCh38",
            "mus_musculus": "GRCm39",
            "rattus_norvegicus": "mRatBN7.2",
            "danio_rerio": "GRCz11",
            "drosophila_melanogaster": "BDGP6.46",
            "caenorhabditis_elegans": "WBcel235",
            "saccharomyces_cerevisiae": "R64-1-1",
        }
        assembly = assembly_map.get(self.species, "unknown")

        file_name = file_pattern.format(
            species_capitalized=species_capitalized,
            assembly=assembly,
            version=version
        )

        # 构建下载源
        sources = [
            DownloadSource(
                url=f"{self.BASE_URL}/{path}{file_name}",
                protocol="https",
                priority=1,
                is_mirror=False,
                region="UK",
            )
        ]

        # 添加镜像源
        for region, mirror_url in self.MIRRORS.items():
            sources.append(
                DownloadSource(
                    url=f"{mirror_url}{path}{file_name}",
                    protocol="https",
                    priority=2,
                    is_mirror=True,
                    region=region,
                )
            )

        # 根据数据库类型确定格式
        formats = ["fasta"] if self.db_type in ["genome", "cdna", "ncrna", "pep"] else []
        if self.db_type == "gtf":
            formats = ["gtf"]
        elif self.db_type == "gff3":
            formats = ["gff3"]
        elif self.db_type == "variation":
            formats = ["vcf"]

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=f"{db_info.get('display_name', 'Ensembl')} - {species_display}",
            description=db_info.get("description", ""),
            size=0,
            file_count=len(sources),
            formats=formats,
            download_sources=sources,
            checksums={},
            dependencies=["wget", "gzip"],
            license="Apache-2.0",
            website="https://www.ensembl.org/",
            tags=["ensembl", self.db_type, self.species],
            category="annotation" if self.db_type in ["gtf", "gff3"] else "sequence",
        )

    def get_available_versions(self) -> List[str]:
        """获取可用版本列表"""
        return self.SUPPORTED_VERSIONS.copy()

    def get_latest_version(self) -> str:
        """获取最新版本"""
        return self.CURRENT_VERSION

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

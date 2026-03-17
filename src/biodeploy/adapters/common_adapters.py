"""
通用数据库适配器

支持常见生物信息学数据库的下载和安装。
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


# CAZy 数据库配置
CAZY_CONFIG = {
    "base_url": "http://www.cazy.org/",
    "name": "CAZy",
    "description": "Carbohydrate-Active enZYmes Database",
    "files": ["cazy_db.tar.gz"],
    "size": 500 * 1024 * 1024,  # 500MB
}

# CARD/RGI 数据库配置
CARD_CONFIG = {
    "base_url": "https://card.mcmaster.ca/download",
    "name": "CARD/RGI",
    "description": "Comprehensive Antibiotic Resistance Database",
    "files": ["card_database.tar.gz", "rgi.tar.gz"],
    "size": 1 * 1024 * 1024 * 1024,  # 1GB
}

# VFDB 数据库配置
VFDB_CONFIG = {
    "base_url": "http://www.mgc.ac.cn/VFs/",
    "name": "VFDB",
    "description": "Virulence Factor Database",
    "files": ["VFDB.tar.gz"],
    "size": 800 * 1024 * 1024,  # 800MB
}

# GO 数据库配置
GO_CONFIG = {
    "base_url": "http://purl.obolibrary.org/obo/go/",
    "name": "GO",
    "description": "Gene Ontology Database",
    "files": ["go.obo", "go-basic.obo"],
    "size": 100 * 1024 * 1024,  # 100MB
}

# COG 数据库配置
COG_CONFIG = {
    # 最新 COG 数据（例如 COG2024）目录下文件名为 cog-24.*
    "base_url": "https://ftp.ncbi.nih.gov/pub/COG/COG2024/data/",
    "name": "COG",
    "description": "Clusters of Orthologous Groups",
    "files": ["cog-24.def.tab", "cog-24.fun.tab", "cog-24.org.csv"],
    "size": 50 * 1024 * 1024,  # 50MB
}

# Swiss-Prot 数据库配置
SWISSPROT_CONFIG = {
    "base_url": "https://ftp.expasy.org/databases/uniprot/current_release/knowledgebase/",
    "name": "Swiss-Prot",
    "description": "Swiss-Prot Protein Database",
    "files": ["uniprot_sprot.fasta.gz", "uniprot_sprot.xml.gz"],
    "size": 5 * 1024 * 1024 * 1024,  # 5GB
}


@register_adapter
class CAZyAdapter(BaseAdapter):
    """CAZy 数据库适配器"""

    def __init__(self) -> None:
        self.config = CAZY_CONFIG
        self.logger = get_logger("cazy_adapter")
        self.download_service = DownloadService()

    @property
    def database_name(self) -> str:
        return "cazy"

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        if version is None:
            version = self.get_latest_version()

        sources = [
            DownloadSource(
                url=f"{self.config['base_url']}cazy_db.tar.gz",
                protocol="http",
                priority=1,
            )
        ]

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.config["name"],
            description=self.config["description"],
            size=self.config["size"],
            file_count=len(self.config["files"]),
            formats=["tar.gz"],
            download_sources=sources,
            checksums={},
            dependencies=["wget"],
            license="Academic",
            website="http://www.cazy.org/",
            tags=["cazy", "enzyme", "carbohydrate"],
            category="enzyme",
            last_updated=datetime.now(),
        )

    def get_available_versions(self) -> List[str]:
        return ["latest"]

    def get_latest_version(self) -> str:
        return "latest"

    def download(
        self,
        version: str,
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        target_path = Path(target_path)
        options = options or {}

        self.logger.info(f"开始下载 {self.database_name}")

        metadata = self.get_metadata(version)

        for source in metadata.download_sources:
            file_name = source.url.split("/")[-1]
            file_path = target_path / file_name

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

        return True

    def install(
        self,
        source_path: Path,
        install_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        source_path = Path(source_path)
        install_path = Path(install_path)
        options = options or {}

        self.logger.info(f"开始安装 {self.database_name}")

        try:
            FileSystem.ensure_directory(install_path)

            # 解压文件
            import tarfile
            for tar_file in source_path.glob("*.tar.gz"):
                with tarfile.open(tar_file, "r:gz") as tar:
                    tar.extractall(path=install_path)

            if not self.verify(install_path):
                raise DatabaseError(
                    "安装验证失败",
                    ErrorCode.INSTALL_FAILED,
                    {"path": str(install_path)},
                )

            return True
        except Exception as e:
            self.logger.error(f"安装失败：{e}")
            return False

    def verify(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        return install_path.exists() and len(list(install_path.rglob("*"))) > 0

    def uninstall(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        if not install_path.exists():
            return True
        try:
            FileSystem.safe_remove(install_path)
            return True
        except Exception:
            return False

    def get_download_size(self, version: Optional[str] = None) -> int:
        return self.config["size"]


@register_adapter
class CARDAdapter(BaseAdapter):
    """CARD/RGI 数据库适配器"""

    def __init__(self) -> None:
        self.config = CARD_CONFIG
        self.logger = get_logger("card_adapter")
        self.download_service = DownloadService()

    @property
    def database_name(self) -> str:
        return "card_rgi"

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        if version is None:
            version = self.get_latest_version()

        sources = [
            DownloadSource(
                url=f"{self.config['base_url']}/card_database.tar.gz",
                protocol="https",
                priority=1,
            )
        ]

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.config["name"],
            description=self.config["description"],
            size=self.config["size"],
            file_count=len(self.config["files"]),
            formats=["tar.gz"],
            download_sources=sources,
            checksums={},
            dependencies=["rgi"],
            license="Academic",
            website="https://card.mcmaster.ca/",
            tags=["card", "antibiotic", "resistance"],
            category="resistance",
            last_updated=datetime.now(),
        )

    def get_available_versions(self) -> List[str]:
        return ["latest"]

    def get_latest_version(self) -> str:
        return "latest"

    def download(
        self,
        version: str,
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        target_path = Path(target_path)
        options = options or {}

        self.logger.info(f"开始下载 {self.database_name}")

        metadata = self.get_metadata(version)

        for source in metadata.download_sources:
            file_name = source.url.split("/")[-1]
            file_path = target_path / file_name

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

        return True

    def install(
        self,
        source_path: Path,
        install_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        source_path = Path(source_path)
        install_path = Path(install_path)
        options = options or {}

        self.logger.info(f"开始安装 {self.database_name}")

        try:
            FileSystem.ensure_directory(install_path)

            import tarfile
            for tar_file in source_path.glob("*.tar.gz"):
                with tarfile.open(tar_file, "r:gz") as tar:
                    tar.extractall(path=install_path)

            if not self.verify(install_path):
                raise DatabaseError(
                    "安装验证失败",
                    ErrorCode.INSTALL_FAILED,
                    {"path": str(install_path)},
                )

            return True
        except Exception as e:
            self.logger.error(f"安装失败：{e}")
            return False

    def verify(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        return install_path.exists() and len(list(install_path.rglob("*"))) > 0

    def uninstall(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        if not install_path.exists():
            return True
        try:
            FileSystem.safe_remove(install_path)
            return True
        except Exception:
            return False

    def get_download_size(self, version: Optional[str] = None) -> int:
        return self.config["size"]


@register_adapter
class VFDBAdapter(BaseAdapter):
    """VFDB 数据库适配器"""

    def __init__(self) -> None:
        self.config = VFDB_CONFIG
        self.logger = get_logger("vfdb_adapter")
        self.download_service = DownloadService()

    @property
    def database_name(self) -> str:
        return "vfdb"

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        if version is None:
            version = self.get_latest_version()

        sources = [
            DownloadSource(
                url=f"{self.config['base_url']}VFDB.tar.gz",
                protocol="http",
                priority=1,
            )
        ]

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.config["name"],
            description=self.config["description"],
            size=self.config["size"],
            file_count=len(self.config["files"]),
            formats=["tar.gz"],
            download_sources=sources,
            checksums={},
            dependencies=["wget"],
            license="Academic",
            website="http://www.mgc.ac.cn/VFs/",
            tags=["vfdb", "virulence", "pathogen"],
            category="virulence",
            last_updated=datetime.now(),
        )

    def get_available_versions(self) -> List[str]:
        return ["latest"]

    def get_latest_version(self) -> str:
        return "latest"

    def download(
        self,
        version: str,
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        target_path = Path(target_path)
        options = options or {}

        self.logger.info(f"开始下载 {self.database_name}")
        metadata = self.get_metadata(version)

        for source in metadata.download_sources:
            file_name = source.url.split("/")[-1]
            file_path = target_path / file_name

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

        return True

    def install(
        self,
        source_path: Path,
        install_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        source_path = Path(source_path)
        install_path = Path(install_path)
        options = options or {}

        self.logger.info(f"开始安装 {self.database_name}")

        try:
            FileSystem.ensure_directory(install_path)

            import tarfile
            for tar_file in source_path.glob("*.tar.gz"):
                with tarfile.open(tar_file, "r:gz") as tar:
                    tar.extractall(path=install_path)

            if not self.verify(install_path):
                raise DatabaseError(
                    "安装验证失败",
                    ErrorCode.INSTALL_FAILED,
                    {"path": str(install_path)},
                )

            return True
        except Exception as e:
            self.logger.error(f"安装失败：{e}")
            return False

    def verify(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        return install_path.exists() and len(list(install_path.rglob("*"))) > 0

    def uninstall(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        if not install_path.exists():
            return True
        try:
            FileSystem.safe_remove(install_path)
            return True
        except Exception:
            return False

    def get_download_size(self, version: Optional[str] = None) -> int:
        return self.config["size"]


@register_adapter
class GOAdapter(BaseAdapter):
    """GO 数据库适配器"""

    def __init__(self) -> None:
        self.config = GO_CONFIG
        self.logger = get_logger("go_adapter")
        self.download_service = DownloadService()

    @property
    def database_name(self) -> str:
        return "go"

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        if version is None:
            version = self.get_latest_version()

        sources = []
        for file_name in self.config["files"]:
            sources.append(
                DownloadSource(
                    url=f"{self.config['base_url']}{file_name}",
                    protocol="http",
                    priority=1,
                )
            )

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.config["name"],
            description=self.config["description"],
            size=self.config["size"],
            file_count=len(self.config["files"]),
            formats=["obo"],
            download_sources=sources,
            checksums={},
            dependencies=["wget"],
            license="CC BY 4.0",
            website="http://geneontology.org/",
            tags=["go", "ontology", "annotation"],
            category="ontology",
            last_updated=datetime.now(),
        )

    def get_available_versions(self) -> List[str]:
        return ["latest"]

    def get_latest_version(self) -> str:
        return "latest"

    def download(
        self,
        version: str,
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        target_path = Path(target_path)
        options = options or {}

        self.logger.info(f"开始下载 {self.database_name}")
        metadata = self.get_metadata(version)

        for source in metadata.download_sources:
            file_name = source.url.split("/")[-1]
            file_path = target_path / file_name

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

        return True

    def install(
        self,
        source_path: Path,
        install_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        source_path = Path(source_path)
        install_path = Path(install_path)
        options = options or {}

        self.logger.info(f"开始安装 {self.database_name}")

        try:
            FileSystem.ensure_directory(install_path)

            for file_path in source_path.glob("*"):
                dest_path = install_path / file_path.name
                FileSystem.safe_copy(file_path, dest_path, overwrite=True)

            if not self.verify(install_path):
                raise DatabaseError(
                    "安装验证失败",
                    ErrorCode.INSTALL_FAILED,
                    {"path": str(install_path)},
                )

            return True
        except Exception as e:
            self.logger.error(f"安装失败：{e}")
            return False

    def verify(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        return install_path.exists() and len(list(install_path.rglob("*.obo"))) > 0

    def uninstall(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        if not install_path.exists():
            return True
        try:
            FileSystem.safe_remove(install_path)
            return True
        except Exception:
            return False

    def get_download_size(self, version: Optional[str] = None) -> int:
        return self.config["size"]


@register_adapter
class COGAdapter(BaseAdapter):
    """COG 数据库适配器"""

    def __init__(self) -> None:
        self.config = COG_CONFIG
        self.logger = get_logger("cog_adapter")
        self.download_service = DownloadService()

    @property
    def database_name(self) -> str:
        return "cog"

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        if version is None:
            version = self.get_latest_version()

        sources = []
        for file_name in self.config["files"]:
            sources.append(
                DownloadSource(
                    url=f"{self.config['base_url']}{file_name}",
                    protocol="https",
                    priority=1,
                )
            )

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.config["name"],
            description=self.config["description"],
            size=self.config["size"],
            file_count=len(self.config["files"]),
            formats=["csv", "txt"],
            download_sources=sources,
            checksums={},
            dependencies=["wget"],
            license="Public Domain",
            website="https://www.ncbi.nlm.nih.gov/research/cog/",
            tags=["cog", "ortholog", "classification"],
            category="ortholog",
            last_updated=datetime.now(),
        )

    def get_available_versions(self) -> List[str]:
        return ["latest"]

    def get_latest_version(self) -> str:
        return "latest"

    def download(
        self,
        version: str,
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        target_path = Path(target_path)
        options = options or {}

        self.logger.info(f"开始下载 {self.database_name}")
        metadata = self.get_metadata(version)

        for source in metadata.download_sources:
            file_name = source.url.split("/")[-1]
            file_path = target_path / file_name

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

        return True

    def install(
        self,
        source_path: Path,
        install_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        source_path = Path(source_path)
        install_path = Path(install_path)
        options = options or {}

        self.logger.info(f"开始安装 {self.database_name}")

        try:
            FileSystem.ensure_directory(install_path)

            for file_path in source_path.glob("*"):
                dest_path = install_path / file_path.name
                FileSystem.safe_copy(file_path, dest_path, overwrite=True)

            if not self.verify(install_path):
                raise DatabaseError(
                    "安装验证失败",
                    ErrorCode.INSTALL_FAILED,
                    {"path": str(install_path)},
                )

            return True
        except Exception as e:
            self.logger.error(f"安装失败：{e}")
            return False

    def verify(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        return install_path.exists() and len(list(install_path.rglob("*.csv"))) > 0

    def uninstall(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        if not install_path.exists():
            return True
        try:
            FileSystem.safe_remove(install_path)
            return True
        except Exception:
            return False

    def get_download_size(self, version: Optional[str] = None) -> int:
        return self.config["size"]


@register_adapter
class SwissProtAdapter(BaseAdapter):
    """Swiss-Prot 数据库适配器"""

    def __init__(self) -> None:
        self.config = SWISSPROT_CONFIG
        self.logger = get_logger("swissprot_adapter")
        self.download_service = DownloadService()

    @property
    def database_name(self) -> str:
        return "swissprot"

    def get_metadata(self, version: Optional[str] = None) -> DatabaseMetadata:
        if version is None:
            version = self.get_latest_version()

        sources = []
        for file_name in self.config["files"]:
            sources.append(
                DownloadSource(
                    url=f"{self.config['base_url']}complete/{file_name}",
                    protocol="https",
                    priority=1,
                )
            )

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.config["name"],
            description=self.config["description"],
            size=self.config["size"],
            file_count=len(self.config["files"]),
            formats=["fasta", "xml"],
            download_sources=sources,
            checksums={},
            dependencies=["wget"],
            license="CC BY 4.0",
            website="https://www.uniprot.org/",
            tags=["swissprot", "protein", "annotation"],
            category="sequence",
            last_updated=datetime.now(),
        )

    def get_available_versions(self) -> List[str]:
        return ["latest"]

    def get_latest_version(self) -> str:
        return "latest"

    def download(
        self,
        version: str,
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        target_path = Path(target_path)
        options = options or {}

        self.logger.info(f"开始下载 {self.database_name}")
        metadata = self.get_metadata(version)

        for source in metadata.download_sources:
            file_name = source.url.split("/")[-1]
            file_path = target_path / file_name

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

        return True

    def install(
        self,
        source_path: Path,
        install_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        source_path = Path(source_path)
        install_path = Path(install_path)
        options = options or {}

        self.logger.info(f"开始安装 {self.database_name}")

        try:
            FileSystem.ensure_directory(install_path)

            for file_path in source_path.glob("*.gz"):
                import gzip
                import shutil
                output_file = install_path / file_path.stem
                with gzip.open(file_path, "rb") as f_in:
                    with open(output_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

            if not self.verify(install_path):
                raise DatabaseError(
                    "安装验证失败",
                    ErrorCode.INSTALL_FAILED,
                    {"path": str(install_path)},
                )

            return True
        except Exception as e:
            self.logger.error(f"安装失败：{e}")
            return False

    def verify(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        if not install_path.exists():
            return False
        fasta_files = list(install_path.rglob("*.fasta"))
        xml_files = list(install_path.rglob("*.xml"))
        return len(fasta_files) > 0 or len(xml_files) > 0

    def uninstall(self, install_path: Path) -> bool:
        install_path = Path(install_path)
        if not install_path.exists():
            return True
        try:
            FileSystem.safe_remove(install_path)
            return True
        except Exception:
            return False

    def get_download_size(self, version: Optional[str] = None) -> int:
        return self.config["size"]

"""
eggNOG 数据库适配器

支持 eggNOG 数据库的下载和安装。
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
class EggNOGAdapter(BaseAdapter):
    """eggNOG 数据库适配器

    支持 eggNOG 正交群数据库的下载和安装。
    """

    # eggNOG 5.x 下载站点（旧 eggnogdb.embl.de 已不再提供数据库文件）
    # 参考：eggnog5.embl.de/download/emapperdb-5.0.2/
    BASE_URL = "http://eggnog5.embl.de/download/"
    MIRRORS = {
        "main": "http://eggnogdb.embl.de/download/",
    }

    # 注：不同子库的下载结构随版本变化较大；这里先提供“主 emapperdb”可用的核心文件，
    # 其余子库后续可按实际可用 URL 继续补齐。
    DATABASE_TYPES = {
        "eggnog": {
            "name": "eggNOG (emapperdb)",
            "description": "eggNOG-mapper database (emapperdb) for functional annotation",
            "files": [
                "eggnog.db.gz",
                "eggnog_proteins.dmnd.gz",
                "eggnog_proteins.fa.gz",
                "eggnog.taxa_info.tsv.gz",
            ],
            "subdir": "emapperdb-{version}",
        },
        "fungi": {
            "name": "eggNOG Fungi (emapperdb)",
            "description": "eggNOG-mapper database (emapperdb) - fungi subset",
            "files": [
                "eggnog.db.gz",
                "eggnog_proteins.dmnd.gz",
            ],
            "subdir": "emapperdb-{version}",
        },
        "bacteria": {
            "name": "eggNOG Bacteria (emapperdb)",
            "description": "eggNOG-mapper database (emapperdb) - bacteria subset",
            "files": [
                "eggnog.db.gz",
                "eggnog_proteins.dmnd.gz",
            ],
            "subdir": "emapperdb-{version}",
        },
        "archaea": {
            "name": "eggNOG Archaea (emapperdb)",
            "description": "eggNOG-mapper database (emapperdb) - archaea subset",
            "files": [
                "eggnog.db.gz",
                "eggnog_proteins.dmnd.gz",
            ],
            "subdir": "emapperdb-{version}",
        },
        "metazoa": {
            "name": "eggNOG Metazoa (emapperdb)",
            "description": "eggNOG-mapper database (emapperdb) - metazoa subset",
            "files": [
                "eggnog.db.gz",
                "eggnog_proteins.dmnd.gz",
            ],
            "subdir": "emapperdb-{version}",
        },
    }

    def __init__(self, db_type: str = "eggnog") -> None:
        """初始化 eggNOG 适配器

        Args:
            db_type: 数据库类型 (eggnog, fungi, bacteria, archaea, metazoa)
        """
        if db_type not in self.DATABASE_TYPES:
            raise ValueError(f"不支持的数据库类型：{db_type}")

        self.db_type = db_type
        self.db_info = self.DATABASE_TYPES[db_type]
        self.logger = get_logger(f"eggnog_adapter.{db_type}")
        self.download_service = DownloadService()

    @property
    def database_name(self) -> str:
        """数据库名称"""
        return f"eggnog_{self.db_type}"

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
        subdir_tpl = self.db_info.get("subdir", "{version}")
        subdir = subdir_tpl.format(version=version)
        for file_pattern in self.db_info["files"]:
            url = f"{self.BASE_URL}{subdir}/{file_pattern}"
            sources.append(
                DownloadSource(
                    url=url,
                    protocol="http",
                    priority=1,
                    is_mirror=False,
                )
            )

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.db_info["name"],
            description=self.db_info["description"],
            size=2 * 1024 * 1024 * 1024,  # 2GB (估计值)
            file_count=len(self.db_info["files"]),
            formats=["db", "fasta"],
            download_sources=sources,
            checksums={},
            dependencies=["emapper"],
            license="CC BY 4.0",
            website="http://eggnogdb.embl.de/",
            tags=["eggnog", "ortholog", "functional_annotation"],
            category="annotation",
            last_updated=datetime.now(),
        )

    def get_available_versions(self) -> List[str]:
        """获取可用版本列表

        Returns:
            版本列表
        """
        return ["5.0.2", "5.0.1", "5.0"]

    def get_latest_version(self) -> str:
        """获取最新版本

        Returns:
            最新版本号
        """
        return "5.0.2"

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

            # 复制所有文件到安装目录
            for file_path in source_path.glob("*"):
                dest_path = install_path / file_path.name
                FileSystem.safe_copy(file_path, dest_path, overwrite=True)

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

        # 检查关键文件是否存在
        for file_pattern in self.db_info["files"]:
            file_name = file_pattern.split("/")[-1]
            file_path = install_path / file_name
            if not file_path.exists():
                self.logger.warning(f"文件缺失：{file_path}")
                return False

        return True

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
        return 2 * 1024 * 1024 * 1024  # 2GB

    def get_dependencies(self, version: Optional[str] = None) -> List[str]:
        """获取依赖工具列表

        Args:
            version: 版本号

        Returns:
            依赖列表
        """
        return ["python3", "emapper"]

    def get_system_requirements(self, version: Optional[str] = None) -> Dict[str, Any]:
        """获取系统要求

        Args:
            version: 版本号

        Returns:
            系统要求字典
        """
        return {
            "min_disk_space": 5 * 1024 * 1024 * 1024,  # 5GB
            "min_memory": 4 * 1024 * 1024 * 1024,  # 4GB
            "required_tools": ["python3", "emapper"],
        }

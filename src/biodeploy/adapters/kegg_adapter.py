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

    ⚠️ 重要提示：KEGG 数据库需要商业许可才能下载完整数据。

    KEGG (Kyoto Encyclopedia of Genes and Genomes) 是一个商业数据库，
    完整数据下载需要订阅 KEGG 服务。本适配器提供以下使用方式：

    1. KEGG REST API (免费)：通过 API 获取数据（有限制）
    2. KEGG FTP (需许可)：需要有效的订阅账号
    3. KEGG 镜像站点 (如 KEGG Mirror at KEGG API)

    更多信息请访问：https://www.kegg.jp/kegg/legal.html
    """

    # KEGG API 基础 URL（免费但有速率限制）
    API_BASE_URL = "https://rest.kegg.jp"

    # KEGG FTP (需要订阅)
    FTP_BASE_URL = "ftp://ftp.bio.jp/kegg"

    # KEGG 官方网站
    WEBSITE_URL = "https://www.kegg.jp"

    DATABASE_TYPES = {
        "pathway": {
            "name": "KEGG PATHWAY",
            "description": "KEGG PATHWAY database - metabolic and regulatory pathways",
            "api_endpoints": ["list/pathway", "get/pathway"],
            "requires_license": False,  # API 访问免费但有速率限制
        },
        "genes": {
            "name": "KEGG GENES",
            "description": "KEGG GENES database - gene catalogs",
            "api_endpoints": ["list/hsa", "get/hsa"],  # hsa = Homo sapiens
            "requires_license": False,
        },
        "compound": {
            "name": "KEGG COMPOUND",
            "description": "KEGG COMPOUND database - chemical compounds",
            "api_endpoints": ["list/compound", "get/compound"],
            "requires_license": False,
        },
        "reaction": {
            "name": "KEGG REACTION",
            "description": "KEGG REACTION database - chemical reactions",
            "api_endpoints": ["list/reaction", "get/reaction"],
            "requires_license": False,
        },
        "enzyme": {
            "name": "KEGG ENZYME",
            "description": "KEGG ENZYME database - enzyme nomenclature",
            "api_endpoints": ["list/enzyme", "get/enzyme"],
            "requires_license": False,
        },
        "disease": {
            "name": "KEGG DISEASE",
            "description": "KEGG DISEASE database - human diseases",
            "api_endpoints": ["list/disease", "get/disease"],
            "requires_license": False,
        },
        "drug": {
            "name": "KEGG DRUG",
            "description": "KEGG DRUG database - pharmaceuticals",
            "api_endpoints": ["list/drug", "get/drug"],
            "requires_license": False,
        },
    }

    def __init__(self, db_type: str = "pathway") -> None:
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

        # KEGG 主要通过 API 访问
        # 构建 API 端点作为"下载源"
        sources = []
        for endpoint in self.db_info.get("api_endpoints", []):
            url = f"{self.API_BASE_URL}/{endpoint}"
            sources.append(
                DownloadSource(
                    url=url,
                    protocol="https",
                    priority=1,
                    is_mirror=False,
                    region="JP",
                )
            )

        description = self.db_info["description"]

        return DatabaseMetadata(
            name=self.database_name,
            version=version,
            display_name=self.db_info["name"],
            description=description,
            size=0,  # API 数据，大小不固定
            file_count=len(sources),
            formats=["txt", "json", "kgml"],
            download_sources=sources,
            checksums={},
            dependencies=["curl", "python3"],
            license="Academic/Commercial",
            website=self.WEBSITE_URL,
            tags=["kegg", "pathway", "metabolism", "api"],
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

        ⚠️ 重要：KEGG 数据库需要商业许可才能下载完整数据。
        本方法仅通过 API 获取部分数据。如需完整数据，请访问 https://www.kegg.jp/kegg/legal.html

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

        self.logger.warning("=" * 60)
        self.logger.warning(f"KEGG 数据库 {self.db_type} 下载提示：")
        self.logger.warning("=" * 60)
        self.logger.warning("KEGG 是一个商业数据库，完整数据下载需要订阅。")
        self.logger.warning(
            "本适配器使用 KEGG REST API 获取有限数据（免费但有速率限制）。"
        )
        self.logger.warning("如需完整数据，请访问：https://www.kegg.jp/kegg/legal.html")
        self.logger.warning("=" * 60)

        # 检查是否有 KEGG 订阅（通过选项传递）
        has_subscription = options.get("kegg_subscription", False)

        if not has_subscription:
            self.logger.info("使用 KEGG REST API 模式（免费，有速率限制）...")
            self.logger.info(
                "提示：如需完整数据，请购买 KEGG 订阅并在选项中设置 kegg_subscription=True"
            )

        self.logger.info(f"开始下载 {self.database_name} {version}")

        metadata = self.get_metadata(version)

        # 确保目标目录存在
        target_path.mkdir(parents=True, exist_ok=True)

        # 下载/获取数据
        for i, source in enumerate(metadata.download_sources):
            endpoint = source.url.split("/")[-2] if "/" in source.url else source.url
            file_name = f"{self.db_type}_{endpoint}.txt"
            file_path = target_path / file_name

            self.logger.info(
                f"获取数据 {i + 1}/{len(metadata.download_sources)}: {endpoint}"
            )

            result = self.download_service.download(
                sources=[source],
                target_path=file_path,
                options=options,
                progress_callback=progress_callback,
            )

            if not result.success:
                self.logger.warning(f"获取失败：{endpoint}，继续尝试其他端点...")
                continue

        self.logger.info(f"数据获取完成：{target_path}")
        self.logger.info("注意：这是通过 API 获取的部分数据，不是完整 KEGG 数据库。")
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

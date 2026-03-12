"""
数据库元数据模型

定义数据库的元数据信息，包括基本信息、下载源、校验和等。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DownloadSource:
    """下载源信息

    Attributes:
        url: 下载URL
        protocol: 协议类型 (http, https, ftp, rsync)
        priority: 优先级，数字越小优先级越高
        is_mirror: 是否为镜像源
        region: 地区信息，用于选择最近镜像
    """

    url: str
    protocol: str
    priority: int = 1
    is_mirror: bool = False
    region: Optional[str] = None

    def __post_init__(self) -> None:
        """验证数据"""
        if not self.url:
            raise ValueError("URL不能为空")
        if self.protocol not in ["http", "https", "ftp", "rsync"]:
            raise ValueError(f"不支持的协议: {self.protocol}")
        if self.priority < 1:
            raise ValueError("优先级必须大于等于1")


@dataclass
class DatabaseMetadata:
    """数据库元数据

    包含数据库的完整元数据信息，用于描述数据库的基本属性、下载信息、依赖关系等。

    Attributes:
        name: 数据库名称（唯一标识）
        version: 数据库版本
        display_name: 显示名称
        description: 数据库描述
        size: 数据库大小（字节）
        file_count: 文件数量
        formats: 支持的文件格式列表
        download_sources: 下载源列表
        checksums: 校验和字典 (algorithm -> checksum)
        dependencies: 系统依赖列表
        python_dependencies: Python依赖列表
        license: 许可证信息
        license_url: 许可证URL
        website: 官方网站
        documentation_url: 文档URL
        citation: 引用信息
        install_steps: 安装步骤列表
        post_install_steps: 安装后步骤列表
        index_types: 支持的索引类型列表
        index_config: 索引配置字典
        tags: 标签列表
        category: 分类
        last_updated: 最后更新时间
    """

    # 基本信息
    name: str
    version: str
    display_name: str
    description: str

    # 数据信息
    size: int
    file_count: int
    formats: List[str]

    # 下载信息
    download_sources: List[DownloadSource]
    checksums: Dict[str, str]

    # 依赖信息
    dependencies: List[str] = field(default_factory=list)
    python_dependencies: List[str] = field(default_factory=list)

    # 许可证信息
    license: str = "Unknown"
    license_url: Optional[str] = None

    # 网站信息
    website: str = ""
    documentation_url: Optional[str] = None
    citation: Optional[str] = None

    # 安装信息
    install_steps: List[str] = field(default_factory=list)
    post_install_steps: List[str] = field(default_factory=list)

    # 索引信息
    index_types: List[str] = field(default_factory=list)
    index_config: Dict[str, Any] = field(default_factory=dict)

    # 元数据
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    last_updated: Optional[datetime] = None

    def __post_init__(self) -> None:
        """验证数据"""
        if not self.name:
            raise ValueError("数据库名称不能为空")
        if not self.version:
            raise ValueError("数据库版本不能为空")
        if self.size < 0:
            raise ValueError("数据库大小不能为负数")
        if self.file_count < 0:
            raise ValueError("文件数量不能为负数")

    def get_primary_source(self) -> Optional[DownloadSource]:
        """获取主要下载源（优先级最高的非镜像源）

        Returns:
            主要下载源，如果没有则返回None
        """
        non_mirrors = [s for s in self.download_sources if not s.is_mirror]
        if non_mirrors:
            return min(non_mirrors, key=lambda x: x.priority)
        return None

    def get_best_mirror(self, region: Optional[str] = None) -> Optional[DownloadSource]:
        """获取最佳镜像源

        Args:
            region: 地区信息，用于选择最近的镜像

        Returns:
            最佳镜像源，如果没有则返回None
        """
        mirrors = [s for s in self.download_sources if s.is_mirror]
        if not mirrors:
            return None

        # 如果指定了地区，优先选择该地区的镜像
        if region:
            region_mirrors = [s for s in mirrors if s.region == region]
            if region_mirrors:
                return min(region_mirrors, key=lambda x: x.priority)

        # 否则返回优先级最高的镜像
        return min(mirrors, key=lambda x: x.priority)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            包含所有元数据的字典
        """
        return {
            "name": self.name,
            "version": self.version,
            "display_name": self.display_name,
            "description": self.description,
            "size": self.size,
            "file_count": self.file_count,
            "formats": self.formats,
            "download_sources": [
                {
                    "url": s.url,
                    "protocol": s.protocol,
                    "priority": s.priority,
                    "is_mirror": s.is_mirror,
                    "region": s.region,
                }
                for s in self.download_sources
            ],
            "checksums": self.checksums,
            "dependencies": self.dependencies,
            "python_dependencies": self.python_dependencies,
            "license": self.license,
            "license_url": self.license_url,
            "website": self.website,
            "documentation_url": self.documentation_url,
            "citation": self.citation,
            "install_steps": self.install_steps,
            "post_install_steps": self.post_install_steps,
            "index_types": self.index_types,
            "index_config": self.index_config,
            "tags": self.tags,
            "category": self.category,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

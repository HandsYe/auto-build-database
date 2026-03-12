"""
安装状态模型

定义数据库安装状态和安装记录的数据模型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from biodeploy.models.metadata import DatabaseMetadata


class InstallationStatus(Enum):
    """安装状态枚举

    定义数据库安装过程中的各种状态。
    """

    PENDING = "pending"  # 等待安装
    DOWNLOADING = "downloading"  # 正在下载
    VERIFYING = "verifying"  # 正在校验
    INSTALLING = "installing"  # 正在安装
    INDEXING = "indexing"  # 正在构建索引
    COMPLETED = "completed"  # 安装完成
    FAILED = "failed"  # 安装失败
    ROLLBACK = "rollback"  # 正在回滚
    UPDATING = "updating"  # 正在更新


@dataclass
class InstallationRecord:
    """安装记录

    记录数据库安装的完整信息，包括基本信息、文件信息、配置信息、进度信息等。

    Attributes:
        name: 数据库名称
        version: 数据库版本
        install_path: 安装路径
        install_time: 安装时间
        status: 安装状态
        files: 已安装的文件列表
        total_size: 总大小（字节）
        config_files: 配置文件列表
        index_files: 索引文件列表
        environment_variables: 环境变量字典
        progress: 安装进度 (0.0 - 1.0)
        current_step: 当前步骤描述
        error_message: 错误信息
        error_details: 错误详情
        metadata: 数据库元数据
        last_updated: 最后更新时间
    """

    # 基本信息
    name: str
    version: str

    # 安装信息
    install_path: Path
    install_time: datetime
    status: InstallationStatus

    # 文件信息
    files: List[Path] = field(default_factory=list)
    total_size: int = 0

    # 配置信息
    config_files: List[Path] = field(default_factory=list)
    index_files: List[Path] = field(default_factory=list)

    # 环境变量
    environment_variables: Dict[str, str] = field(default_factory=dict)

    # 进度信息
    progress: float = 0.0
    current_step: str = ""

    # 错误信息
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    # 元数据
    metadata: Optional[DatabaseMetadata] = None
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """验证数据"""
        if not self.name:
            raise ValueError("数据库名称不能为空")
        if not self.version:
            raise ValueError("数据库版本不能为空")
        if not 0.0 <= self.progress <= 1.0:
            raise ValueError("进度必须在0.0到1.0之间")

        # 确保install_path是Path对象
        if isinstance(self.install_path, str):
            self.install_path = Path(self.install_path)

    def update_progress(self, progress: float, step: str = "") -> None:
        """更新进度

        Args:
            progress: 新的进度值 (0.0 - 1.0)
            step: 当前步骤描述
        """
        if not 0.0 <= progress <= 1.0:
            raise ValueError("进度必须在0.0到1.0之间")

        self.progress = progress
        self.current_step = step
        self.last_updated = datetime.now()

    def set_error(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """设置错误信息

        Args:
            message: 错误消息
            details: 错误详情
        """
        self.status = InstallationStatus.FAILED
        self.error_message = message
        self.error_details = details or {}
        self.last_updated = datetime.now()

    def is_completed(self) -> bool:
        """检查是否安装完成

        Returns:
            如果安装完成返回True，否则返回False
        """
        return self.status == InstallationStatus.COMPLETED

    def is_failed(self) -> bool:
        """检查是否安装失败

        Returns:
            如果安装失败返回True，否则返回False
        """
        return self.status == InstallationStatus.FAILED

    def is_in_progress(self) -> bool:
        """检查是否正在安装

        Returns:
            如果正在安装返回True，否则返回False
        """
        return self.status in [
            InstallationStatus.PENDING,
            InstallationStatus.DOWNLOADING,
            InstallationStatus.VERIFYING,
            InstallationStatus.INSTALLING,
            InstallationStatus.INDEXING,
            InstallationStatus.UPDATING,
            InstallationStatus.ROLLBACK,
        ]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            包含所有安装记录的字典
        """
        return {
            "name": self.name,
            "version": self.version,
            "install_path": str(self.install_path),
            "install_time": self.install_time.isoformat(),
            "status": self.status.value,
            "files": [str(f) for f in self.files],
            "total_size": self.total_size,
            "config_files": [str(f) for f in self.config_files],
            "index_files": [str(f) for f in self.index_files],
            "environment_variables": self.environment_variables,
            "progress": self.progress,
            "current_step": self.current_step,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstallationRecord":
        """从字典创建安装记录

        Args:
            data: 包含安装记录的字典

        Returns:
            安装记录对象
        """
        return cls(
            name=data["name"],
            version=data["version"],
            install_path=Path(data["install_path"]),
            install_time=datetime.fromisoformat(data["install_time"]),
            status=InstallationStatus(data["status"]),
            files=[Path(f) for f in data.get("files", [])],
            total_size=data.get("total_size", 0),
            config_files=[Path(f) for f in data.get("config_files", [])],
            index_files=[Path(f) for f in data.get("index_files", [])],
            environment_variables=data.get("environment_variables", {}),
            progress=data.get("progress", 0.0),
            current_step=data.get("current_step", ""),
            error_message=data.get("error_message"),
            error_details=data.get("error_details"),
            last_updated=datetime.fromisoformat(data["last_updated"])
            if "last_updated" in data
            else datetime.now(),
        )

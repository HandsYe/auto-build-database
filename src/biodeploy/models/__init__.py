"""
模型模块

导出所有数据模型。
"""

from biodeploy.models.config import (
    Config,
    DownloadConfig,
    InstallConfig,
    LogConfig,
    NetworkConfig,
    NotificationConfig,
)
from biodeploy.models.errors import (
    BioDeployError,
    ConfigError,
    DatabaseError,
    DownloadError,
    ErrorCode,
    IndexError,
    InstallError,
    StateError,
)
from biodeploy.models.metadata import DatabaseMetadata, DownloadSource
from biodeploy.models.state import InstallationRecord, InstallationStatus

__all__ = [
    # Metadata models
    "DatabaseMetadata",
    "DownloadSource",
    # State models
    "InstallationRecord",
    "InstallationStatus",
    # Config models
    "Config",
    "InstallConfig",
    "NetworkConfig",
    "DownloadConfig",
    "LogConfig",
    "NotificationConfig",
    # Error models
    "ErrorCode",
    "BioDeployError",
    "ConfigError",
    "DownloadError",
    "InstallError",
    "DatabaseError",
    "IndexError",
    "StateError",
]

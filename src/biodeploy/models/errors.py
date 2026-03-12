"""
错误模型

定义系统中的错误类型和错误代码。
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCode(Enum):
    """错误代码枚举

    定义系统中所有可能的错误代码。
    """

    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = 1000
    INVALID_ARGUMENT = 1001
    FILE_NOT_FOUND = 1002
    PERMISSION_DENIED = 1003
    DISK_SPACE_INSUFFICIENT = 1004

    # 配置错误 (2000-2999)
    CONFIG_FILE_NOT_FOUND = 2000
    CONFIG_PARSE_ERROR = 2001
    CONFIG_VALIDATION_ERROR = 2002
    CONFIG_SAVE_ERROR = 2003

    # 下载错误 (3000-3999)
    DOWNLOAD_FAILED = 3000
    DOWNLOAD_TIMEOUT = 3001
    DOWNLOAD_NETWORK_ERROR = 3002
    DOWNLOAD_CHECKSUM_MISMATCH = 3003
    DOWNLOAD_SOURCE_UNAVAILABLE = 3004

    # 安装错误 (4000-4999)
    INSTALL_FAILED = 4000
    INSTALL_DEPENDENCY_MISSING = 4001
    INSTALL_PATH_EXISTS = 4002
    INSTALL_VERSION_CONFLICT = 4003
    INSTALL_ROLLBACK_FAILED = 4004

    # 数据库错误 (5000-5999)
    DATABASE_NOT_FOUND = 5000
    DATABASE_ALREADY_INSTALLED = 5001
    DATABASE_VERSION_NOT_FOUND = 5002
    DATABASE_METADATA_INVALID = 5003
    DATABASE_ADAPTER_NOT_FOUND = 5004

    # 索引错误 (6000-6999)
    INDEX_BUILD_FAILED = 6000
    INDEX_TYPE_NOT_SUPPORTED = 6001
    INDEX_TOOL_NOT_FOUND = 6002

    # 状态错误 (7000-7999)
    STATE_LOAD_ERROR = 7000
    STATE_SAVE_ERROR = 7001
    STATE_CORRUPTED = 7002


class BioDeployError(Exception):
    """BioDeploy基础错误类

    所有BioDeploy错误的基类。

    Attributes:
        error_code: 错误代码
        message: 错误消息
        details: 错误详情
    """

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """初始化错误

        Args:
            error_code: 错误代码
            message: 错误消息
            details: 错误详情
        """
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            包含错误信息的字典
        """
        return {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "message": self.message,
            "details": self.details,
        }


class ConfigError(BioDeployError):
    """配置错误"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.CONFIG_PARSE_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(error_code, message, details)


class DownloadError(BioDeployError):
    """下载错误"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DOWNLOAD_FAILED,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(error_code, message, details)


class InstallError(BioDeployError):
    """安装错误"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INSTALL_FAILED,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(error_code, message, details)


class DatabaseError(BioDeployError):
    """数据库错误"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DATABASE_NOT_FOUND,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(error_code, message, details)


class IndexError(BioDeployError):
    """索引错误"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INDEX_BUILD_FAILED,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(error_code, message, details)


class StateError(BioDeployError):
    """状态错误"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.STATE_LOAD_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(error_code, message, details)

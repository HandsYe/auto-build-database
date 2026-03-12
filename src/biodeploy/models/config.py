"""
配置模型

定义系统配置的数据模型，包括安装配置、网络配置、下载配置等。
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class NetworkConfig:
    """网络配置

    Attributes:
        proxy: 代理服务器地址
        timeout: 超时时间（秒）
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        user_agent: User-Agent字符串
    """

    proxy: Optional[str] = None
    timeout: int = 300
    max_retries: int = 3
    retry_delay: int = 5
    user_agent: str = "biodeploy/1.0"

    def __post_init__(self) -> None:
        """验证数据"""
        if self.timeout < 0:
            raise ValueError("超时时间不能为负数")
        if self.max_retries < 0:
            raise ValueError("最大重试次数不能为负数")
        if self.retry_delay < 0:
            raise ValueError("重试延迟不能为负数")


@dataclass
class DownloadConfig:
    """下载配置

    Attributes:
        max_parallel: 最大并发下载数
        chunk_size: 下载块大小（字节）
        resume_enabled: 是否启用断点续传
        verify_checksum: 是否验证校验和
    """

    max_parallel: int = 3
    chunk_size: int = 8192
    resume_enabled: bool = True
    verify_checksum: bool = True

    def __post_init__(self) -> None:
        """验证数据"""
        if self.max_parallel < 1:
            raise ValueError("最大并发数必须大于0")
        if self.chunk_size < 1024:
            raise ValueError("下载块大小必须大于等于1024字节")


@dataclass
class InstallConfig:
    """安装配置

    Attributes:
        default_install_path: 默认安装路径
        temp_path: 临时文件路径
        auto_cleanup: 是否自动清理临时文件
        force_reinstall: 是否强制重新安装
        skip_dependencies: 是否跳过依赖检查
    """

    default_install_path: Path
    temp_path: Path = field(default_factory=lambda: Path("/tmp/biodeploy"))
    auto_cleanup: bool = True
    force_reinstall: bool = False
    skip_dependencies: bool = False

    def __post_init__(self) -> None:
        """验证数据并转换路径"""
        if isinstance(self.default_install_path, str):
            self.default_install_path = Path(self.default_install_path)
        if isinstance(self.temp_path, str):
            self.temp_path = Path(self.temp_path)


@dataclass
class LogConfig:
    """日志配置

    Attributes:
        level: 日志级别
        log_path: 日志文件路径
        max_size: 日志文件最大大小（字节）
        backup_count: 日志备份数量
        format: 日志格式
    """

    level: str = "INFO"
    log_path: Path = field(default_factory=lambda: Path("~/.biodeploy/logs"))
    max_size: int = 100 * 1024 * 1024  # 100MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __post_init__(self) -> None:
        """验证数据"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"无效的日志级别: {self.level}")

        self.level = self.level.upper()

        if isinstance(self.log_path, str):
            self.log_path = Path(self.log_path)

        if self.max_size < 1024 * 1024:  # 最小1MB
            raise ValueError("日志文件最大大小必须大于等于1MB")


@dataclass
class NotificationConfig:
    """通知配置

    Attributes:
        enabled: 是否启用通知
        email: 邮件地址
        slack_webhook: Slack Webhook URL
        on_success: 安装成功时是否通知
        on_failure: 安装失败时是否通知
    """

    enabled: bool = False
    email: Optional[str] = None
    slack_webhook: Optional[str] = None
    on_success: bool = True
    on_failure: bool = True


@dataclass
class Config:
    """全局配置

    Attributes:
        version: 配置版本
        install: 安装配置
        network: 网络配置
        download: 下载配置
        log: 日志配置
        notification: 通知配置
        mirrors: 镜像源配置
        databases: 数据库特定配置
    """

    # 版本信息
    version: str = "1.0.0"

    # 安装配置
    install: InstallConfig = field(
        default_factory=lambda: InstallConfig(default_install_path=Path.home() / "bio_databases")
    )

    # 网络配置
    network: NetworkConfig = field(default_factory=NetworkConfig)

    # 下载配置
    download: DownloadConfig = field(default_factory=DownloadConfig)

    # 日志配置
    log: LogConfig = field(default_factory=LogConfig)

    # 通知配置
    notification: NotificationConfig = field(default_factory=NotificationConfig)

    # 镜像源配置
    mirrors: Dict[str, List[str]] = field(default_factory=dict)

    # 数据库特定配置
    databases: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            包含所有配置的字典
        """
        return {
            "version": self.version,
            "install": {
                "default_install_path": str(self.install.default_install_path),
                "temp_path": str(self.install.temp_path),
                "auto_cleanup": self.install.auto_cleanup,
                "force_reinstall": self.install.force_reinstall,
                "skip_dependencies": self.install.skip_dependencies,
            },
            "network": {
                "proxy": self.network.proxy,
                "timeout": self.network.timeout,
                "max_retries": self.network.max_retries,
                "retry_delay": self.network.retry_delay,
                "user_agent": self.network.user_agent,
            },
            "download": {
                "max_parallel": self.download.max_parallel,
                "chunk_size": self.download.chunk_size,
                "resume_enabled": self.download.resume_enabled,
                "verify_checksum": self.download.verify_checksum,
            },
            "log": {
                "level": self.log.level,
                "log_path": str(self.log.log_path),
                "max_size": self.log.max_size,
                "backup_count": self.log.backup_count,
                "format": self.log.format,
            },
            "notification": {
                "enabled": self.notification.enabled,
                "email": self.notification.email,
                "slack_webhook": self.notification.slack_webhook,
                "on_success": self.notification.on_success,
                "on_failure": self.notification.on_failure,
            },
            "mirrors": self.mirrors,
            "databases": self.databases,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """从字典创建配置

        Args:
            data: 包含配置的字典

        Returns:
            配置对象
        """
        install_data = data.get("install", {})
        network_data = data.get("network", {})
        download_data = data.get("download", {})
        log_data = data.get("log", {})
        notification_data = data.get("notification", {})

        return cls(
            version=data.get("version", "1.0.0"),
            install=InstallConfig(
                default_install_path=Path(install_data.get("default_install_path", Path.home() / "bio_databases")),
                temp_path=Path(install_data.get("temp_path", "/tmp/biodeploy")),
                auto_cleanup=install_data.get("auto_cleanup", True),
                force_reinstall=install_data.get("force_reinstall", False),
                skip_dependencies=install_data.get("skip_dependencies", False),
            ),
            network=NetworkConfig(
                proxy=network_data.get("proxy"),
                timeout=network_data.get("timeout", 300),
                max_retries=network_data.get("max_retries", 3),
                retry_delay=network_data.get("retry_delay", 5),
                user_agent=network_data.get("user_agent", "biodeploy/1.0"),
            ),
            download=DownloadConfig(
                max_parallel=download_data.get("max_parallel", 3),
                chunk_size=download_data.get("chunk_size", 8192),
                resume_enabled=download_data.get("resume_enabled", True),
                verify_checksum=download_data.get("verify_checksum", True),
            ),
            log=LogConfig(
                level=log_data.get("level", "INFO"),
                log_path=Path(log_data.get("log_path", "~/.biodeploy/logs")),
                max_size=log_data.get("max_size", 100 * 1024 * 1024),
                backup_count=log_data.get("backup_count", 5),
                format=log_data.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            ),
            notification=NotificationConfig(
                enabled=notification_data.get("enabled", False),
                email=notification_data.get("email"),
                slack_webhook=notification_data.get("slack_webhook"),
                on_success=notification_data.get("on_success", True),
                on_failure=notification_data.get("on_failure", True),
            ),
            mirrors=data.get("mirrors", {}),
            databases=data.get("databases", {}),
        )

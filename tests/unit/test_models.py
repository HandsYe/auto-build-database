"""
单元测试 - 数据模型

测试数据模型的创建和验证。
"""

import pytest
from datetime import datetime
from pathlib import Path
from biodeploy.models import (
    DatabaseMetadata,
    DownloadSource,
    InstallationRecord,
    InstallationStatus,
    Config,
    InstallConfig,
    NetworkConfig,
    DownloadConfig,
    LogConfig,
)


class TestDownloadSource:
    """测试DownloadSource模型"""

    def test_create_download_source(self):
        """测试创建下载源"""
        source = DownloadSource(
            url="https://example.com/file.tar.gz",
            protocol="https",
            priority=1,
            is_mirror=False,
        )
        assert source.url == "https://example.com/file.tar.gz"
        assert source.protocol == "https"
        assert source.priority == 1
        assert not source.is_mirror

    def test_invalid_protocol(self):
        """测试无效协议"""
        with pytest.raises(ValueError, match="不支持的协议"):
            DownloadSource(url="https://example.com", protocol="invalid")

    def test_empty_url(self):
        """测试空URL"""
        with pytest.raises(ValueError, match="URL不能为空"):
            DownloadSource(url="", protocol="https")


class TestDatabaseMetadata:
    """测试DatabaseMetadata模型"""

    def test_create_metadata(self):
        """测试创建数据库元数据"""
        source = DownloadSource(
            url="https://example.com/db.tar.gz",
            protocol="https",
        )
        metadata = DatabaseMetadata(
            name="test_db",
            version="1.0.0",
            display_name="Test Database",
            description="A test database",
            size=1024 * 1024 * 100,  # 100MB
            file_count=10,
            formats=["fasta", "gff"],
            download_sources=[source],
            checksums={"sha256": "abc123"},
        )
        assert metadata.name == "test_db"
        assert metadata.version == "1.0.0"
        assert metadata.size == 1024 * 1024 * 100

    def test_get_primary_source(self):
        """测试获取主要下载源"""
        source1 = DownloadSource(url="https://mirror.com/db", protocol="https", priority=2, is_mirror=True)
        source2 = DownloadSource(url="https://primary.com/db", protocol="https", priority=1, is_mirror=False)

        metadata = DatabaseMetadata(
            name="test",
            version="1.0",
            display_name="Test",
            description="Test",
            size=1000,
            file_count=1,
            formats=["fasta"],
            download_sources=[source1, source2],
            checksums={},
        )

        primary = metadata.get_primary_source()
        assert primary is not None
        assert primary.url == "https://primary.com/db"


class TestInstallationRecord:
    """测试InstallationRecord模型"""

    def test_create_record(self):
        """测试创建安装记录"""
        record = InstallationRecord(
            name="test_db",
            version="1.0.0",
            install_path=Path("/data/test_db"),
            install_time=datetime.now(),
            status=InstallationStatus.PENDING,
        )
        assert record.name == "test_db"
        assert record.status == InstallationStatus.PENDING
        assert record.progress == 0.0

    def test_update_progress(self):
        """测试更新进度"""
        record = InstallationRecord(
            name="test",
            version="1.0",
            install_path=Path("/data/test"),
            install_time=datetime.now(),
            status=InstallationStatus.DOWNLOADING,
        )

        record.update_progress(0.5, "正在下载")
        assert record.progress == 0.5
        assert record.current_step == "正在下载"

    def test_invalid_progress(self):
        """测试无效进度值"""
        record = InstallationRecord(
            name="test",
            version="1.0",
            install_path=Path("/data/test"),
            install_time=datetime.now(),
            status=InstallationStatus.PENDING,
        )

        with pytest.raises(ValueError, match="进度必须在0.0到1.0之间"):
            record.update_progress(1.5)


class TestConfig:
    """测试Config模型"""

    def test_create_config(self):
        """测试创建配置"""
        config = Config()
        assert config.version == "1.0.0"
        assert config.install.default_install_path == Path.home() / "bio_databases"

    def test_config_to_dict(self):
        """测试配置转换为字典"""
        config = Config()
        data = config.to_dict()
        assert "version" in data
        assert "install" in data
        assert "network" in data

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "version": "1.0.0",
            "install": {
                "default_install_path": "/data/bio",
                "temp_path": "/tmp/bio",
            },
        }
        config = Config.from_dict(data)
        assert config.install.default_install_path == Path("/data/bio")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

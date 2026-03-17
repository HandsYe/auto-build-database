"""
单元测试 - 安装管理器

测试安装管理器的功能。
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from biodeploy.core.installation_manager import InstallationManager
from biodeploy.models.state import InstallationRecord, InstallationStatus
from biodeploy.models.metadata import DatabaseMetadata, DownloadSource
from biodeploy.adapters.base_adapter import BaseAdapter


class MockAdapter(BaseAdapter):
    """模拟适配器"""

    @property
    def database_name(self) -> str:
        return "test_db"

    def get_metadata(self, version=None):
        return DatabaseMetadata(
            name="test_db",
            version=version or "1.0.0",
            display_name="Test Database",
            description="A test database",
            size=1024 * 1024 * 100,
            file_count=10,
            formats=["fasta"],
            download_sources=[
                DownloadSource(url="https://example.com/db.tar.gz", protocol="https")
            ],
            checksums={},
            index_types=["blast"],
        )

    def get_available_versions(self):
        return ["1.0.0", "1.1.0", "2.0.0"]

    def download(self, version, target_path, options=None, progress_callback=None):
        # 模拟下载成功
        target_path.write_bytes(b"test data")
        return True

    def install(self, source_path, install_path, options=None):
        # 模拟安装成功
        install_path.mkdir(parents=True, exist_ok=True)
        (install_path / "test.txt").write_text("installed")
        return True

    def verify(self, install_path):
        # 模拟验证成功
        return install_path.exists()

    def uninstall(self, install_path):
        # 模拟卸载成功
        return True


class TestInstallationManager:
    """测试InstallationManager"""

    @pytest.fixture
    def mock_registry(self):
        """创建模拟注册表"""
        registry = Mock()
        registry.get.return_value = MockAdapter()
        return registry

    @pytest.fixture
    def mock_state_manager(self):
        """创建模拟状态管理器"""
        manager = Mock()
        manager.is_installed.return_value = False
        manager.save_record = Mock()
        return manager

    @pytest.fixture
    def installation_manager(self, mock_registry, mock_state_manager, tmp_path):
        """创建安装管理器实例"""
        return InstallationManager(
            state_manager=mock_state_manager,
            registry=mock_registry,
            install_path=tmp_path / "databases",
        )

    def test_create_installation_manager(self, installation_manager):
        """测试创建安装管理器"""
        assert installation_manager._install_path is not None
        assert installation_manager._download_service is not None
        assert installation_manager._index_service is not None

    def test_install_database_not_found(self, installation_manager, mock_registry):
        """测试安装不存在的数据库"""
        mock_registry.get.return_value = None
        
        result = installation_manager.install("nonexistent_db")
        
        assert not result
        mock_registry.get.assert_called_once_with("nonexistent_db")

    @patch('biodeploy.core.installation_manager.FileSystem')
    def test_install_success(
        self,
        mock_filesystem,
        installation_manager,
        mock_state_manager,
        tmp_path
    ):
        """测试成功安装"""
        # 模拟文件系统操作
        mock_filesystem.ensure_directory = Mock()
        mock_filesystem.list_files = Mock(return_value=[])
        mock_filesystem.get_directory_size = Mock(return_value=1024)
        mock_filesystem.check_disk_space = Mock(return_value=True)
        mock_filesystem.get_disk_usage = Mock(return_value={"free": 1024 * 1024 * 1024})
        mock_filesystem.safe_remove = Mock()

        result = installation_manager.install("test_db", install_path=tmp_path / "test_install")

        assert result
        # 验证状态记录被保存
        assert mock_state_manager.save_record.called

    def test_install_already_installed(
        self,
        installation_manager,
        mock_state_manager,
        mock_registry
    ):
        """测试已安装的数据库"""
        mock_state_manager.is_installed.return_value = True
        
        result = installation_manager.install("test_db")
        
        assert result  # 应该返回True，跳过安装

    @patch('biodeploy.core.installation_manager.FileSystem')
    def test_install_with_force(
        self,
        mock_filesystem,
        installation_manager,
        mock_state_manager,
        tmp_path
    ):
        """测试强制重新安装"""
        mock_state_manager.is_installed.return_value = True
        
        # 模拟文件系统操作
        mock_filesystem.ensure_directory = Mock()
        mock_filesystem.list_files = Mock(return_value=[])
        mock_filesystem.get_directory_size = Mock(return_value=1024)
        mock_filesystem.check_disk_space = Mock(return_value=True)
        mock_filesystem.get_disk_usage = Mock(return_value={"free": 1024 * 1024 * 1024})
        mock_filesystem.safe_remove = Mock()

        result = installation_manager.install(
            "test_db",
            install_path=tmp_path / "test_install",
            options={"force": True}
        )

        assert result
        # 验证强制重新安装时仍然执行了安装流程

    def test_install_multiple_serial(self, installation_manager, mock_registry):
        """测试批量串行安装"""
        databases = ["db1", "db2", "db3"]
        
        # 模拟所有数据库都安装成功
        with patch.object(installation_manager, 'install', return_value=True):
            results = installation_manager.install_multiple(
                databases,
                options={"parallel": False}
            )

        assert len(results) == 3
        assert all(results.values())

    def test_install_multiple_parallel(self, installation_manager, mock_registry):
        """测试批量并行安装"""
        databases = ["db1", "db2", "db3"]
        
        # 模拟所有数据库都安装成功
        with patch.object(installation_manager, 'install', return_value=True):
            results = installation_manager.install_multiple(
                databases,
                options={"parallel": True, "max_parallel": 2}
            )

        assert len(results) == 3
        assert all(results.values())

    def test_check_dependencies_skip(self, installation_manager):
        """测试跳过依赖检查"""
        adapter = MockAdapter()
        result = installation_manager._check_dependencies(
            adapter,
            {"skip_deps": True}
        )
        assert result

    def test_check_dependencies_success(self, installation_manager):
        """测试依赖检查成功"""
        adapter = MockAdapter()
        
        with patch.object(
            installation_manager._dep_manager,
            'check_dependencies',
            return_value=(["tool1"], [])
        ):
            result = installation_manager._check_dependencies(adapter, {})
            assert result

    def test_check_dependencies_missing(self, installation_manager):
        """测试缺少依赖"""
        adapter = MockAdapter()
        
        with patch.object(
            installation_manager._dep_manager,
            'check_dependencies',
            return_value=(["tool1"], ["tool2"])
        ):
            result = installation_manager._check_dependencies(adapter, {})
            assert not result

    @patch('biodeploy.core.installation_manager.FileSystem')
    def test_check_disk_space_sufficient(
        self,
        mock_filesystem,
        installation_manager,
        tmp_path
    ):
        """测试磁盘空间充足"""
        adapter = MockAdapter()
        
        mock_filesystem.check_disk_space.return_value = True
        mock_filesystem.get_disk_usage.return_value = {"free": 1024 * 1024 * 1024}
        
        result = installation_manager._check_disk_space(
            adapter,
            "1.0.0",
            tmp_path
        )
        
        assert result

    @patch('biodeploy.core.installation_manager.FileSystem')
    def test_check_disk_space_insufficient(
        self,
        mock_filesystem,
        installation_manager,
        tmp_path
    ):
        """测试磁盘空间不足"""
        adapter = MockAdapter()
        
        mock_filesystem.check_disk_space.return_value = False
        mock_filesystem.get_disk_usage.return_value = {"free": 1024}
        
        result = installation_manager._check_disk_space(
            adapter,
            "1.0.0",
            tmp_path
        )
        
        assert not result

    def test_notify_progress(self, installation_manager):
        """测试进度通知"""
        callback = Mock()
        installation_manager._notify_progress(callback, "测试消息", 0.5)
        
        callback.assert_called_once_with("测试消息", 0.5)

    def test_notify_progress_callback_error(self, installation_manager):
        """测试进度回调出错"""
        callback = Mock(side_effect=Exception("Callback error"))
        
        # 不应该抛出异常
        installation_manager._notify_progress(callback, "测试消息", 0.5)

    def test_installation_context(self, installation_manager, tmp_path):
        """测试安装上下文管理器"""
        temp_path = tmp_path / "temp" / "test.tar.gz"
        
        with installation_manager._installation_context("test_db", "1.0.0", temp_path) as path:
            assert path == temp_path
            assert temp_path.parent.exists()

    def test_installation_context_cleanup_on_error(self, installation_manager, tmp_path):
        """测试安装上下文在出错时清理"""
        temp_path = tmp_path / "temp" / "test.tar.gz"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_bytes(b"test data")
        
        with pytest.raises(Exception):
            with installation_manager._installation_context("test_db", "1.0.0", temp_path):
                raise Exception("Test error")
        
        # 临时文件应该被清理
        assert not temp_path.exists()


class TestInstallationRecord:
    """测试InstallationRecord"""

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

    def test_set_error(self):
        """测试设置错误"""
        record = InstallationRecord(
            name="test",
            version="1.0",
            install_path=Path("/data/test"),
            install_time=datetime.now(),
            status=InstallationStatus.INSTALLING,
        )
        
        record.set_error("安装失败", {"reason": "磁盘空间不足"})
        
        assert record.status == InstallationStatus.FAILED
        assert record.error_message == "安装失败"
        assert record.error_details["reason"] == "磁盘空间不足"

    def test_is_completed(self):
        """测试是否完成"""
        record = InstallationRecord(
            name="test",
            version="1.0",
            install_path=Path("/data/test"),
            install_time=datetime.now(),
            status=InstallationStatus.COMPLETED,
        )
        
        assert record.is_completed()

    def test_is_failed(self):
        """测试是否失败"""
        record = InstallationRecord(
            name="test",
            version="1.0",
            install_path=Path("/data/test"),
            install_time=datetime.now(),
            status=InstallationStatus.FAILED,
        )
        
        assert record.is_failed()

    def test_is_in_progress(self):
        """测试是否进行中"""
        for status in [
            InstallationStatus.PENDING,
            InstallationStatus.DOWNLOADING,
            InstallationStatus.VERIFYING,
            InstallationStatus.INSTALLING,
        ]:
            record = InstallationRecord(
                name="test",
                version="1.0",
                install_path=Path("/data/test"),
                install_time=datetime.now(),
                status=status,
            )
            assert record.is_in_progress()

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        original = InstallationRecord(
            name="test",
            version="1.0",
            install_path=Path("/data/test"),
            install_time=datetime.now(),
            status=InstallationStatus.COMPLETED,
            files=[Path("/data/test/file1.txt")],
            total_size=1024,
        )
        
        data = original.to_dict()
        restored = InstallationRecord.from_dict(data)
        
        assert restored.name == original.name
        assert restored.version == original.version
        assert restored.status == original.status
        assert restored.total_size == original.total_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

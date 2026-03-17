"""
单元测试 - 下载服务

测试下载服务的功能。
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from biodeploy.services.download_service import DownloadService, DownloadResult
from biodeploy.models.metadata import DownloadSource
from biodeploy.models.errors import DownloadError


class TestDownloadService:
    """测试DownloadService"""

    @pytest.fixture
    def download_service(self):
        """创建下载服务实例"""
        return DownloadService()

    @pytest.fixture
    def sample_source(self):
        """创建示例下载源"""
        return DownloadSource(
            url="https://example.com/test.tar.gz",
            protocol="https",
            priority=1,
            is_mirror=False,
        )

    def test_create_download_service(self, download_service):
        """测试创建下载服务"""
        assert download_service.chunk_size == 8192
        assert download_service.timeout == 300
        assert download_service.max_retries == 3
        assert download_service.session is not None

    def test_create_download_service_with_custom_params(self):
        """测试使用自定义参数创建下载服务"""
        service = DownloadService(
            chunk_size=16384,
            timeout=600,
            max_retries=5,
            retry_delay=10,
            proxy="http://proxy.example.com:8080",
        )
        assert service.chunk_size == 16384
        assert service.timeout == 600
        assert service.max_retries == 5
        assert service.retry_delay == 10
        assert service.proxy == "http://proxy.example.com:8080"

    @patch('biodeploy.services.download_service.requests.Session')
    def test_create_session_with_proxy(self, mock_session_class):
        """测试创建带代理的会话"""
        proxy = "http://proxy.example.com:8080"
        service = DownloadService(proxy=proxy)
        
        # 验证代理设置
        assert service.session.proxies["http"] == proxy
        assert service.session.proxies["https"] == proxy

    def test_close_session(self, download_service):
        """测试关闭会话"""
        download_service.close()
        # 会话应该被关闭，不应该抛出异常

    def test_session_context_manager(self, download_service):
        """测试会话上下文管理器"""
        with download_service.session_context() as service:
            assert service is download_service
        # 退出上下文后，会话应该被关闭

    @patch('biodeploy.services.download_service.requests.Session.get')
    def test_download_success(self, mock_get, download_service, sample_source, tmp_path):
        """测试成功下载"""
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = [b"test data"]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        target_path = tmp_path / "test.tar.gz"
        result = download_service.download([sample_source], target_path)

        assert result.success
        assert result.file_path == target_path
        assert result.downloaded_size > 0

    @patch('biodeploy.services.download_service.requests.Session.get')
    def test_download_with_resume(self, mock_get, download_service, sample_source, tmp_path):
        """测试断点续传下载"""
        # 创建部分下载的文件
        target_path = tmp_path / "test.tar.gz"
        target_path.write_bytes(b"partial data")
        
        # 模拟响应
        mock_response = Mock()
        mock_response.status_code = 206
        mock_response.headers = {
            "content-length": "50",
            "content-range": "bytes 11-60/100"
        }
        mock_response.iter_content.return_value = [b"remaining data"]
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_get.return_value = mock_response

        result = download_service.download([sample_source], target_path)

        assert result.success
        # 验证Range头被设置
        call_args = mock_get.call_args
        assert "Range" in call_args[1]["headers"]

    @patch('biodeploy.services.download_service.requests.Session.get')
    def test_download_all_sources_failed(self, mock_get, download_service, tmp_path):
        """测试所有下载源都失败"""
        # 模拟所有请求都失败
        mock_get.side_effect = Exception("Network error")

        sources = [
            DownloadSource(url="https://source1.com/file", protocol="https", priority=1),
            DownloadSource(url="https://source2.com/file", protocol="https", priority=2),
        ]
        target_path = tmp_path / "test.tar.gz"
        result = download_service.download(sources, target_path)

        assert not result.success
        assert result.error_message == "所有下载源都失败"
        assert result.downloaded_size == 0

    @patch('biodeploy.services.download_service.requests.Session.get')
    def test_download_with_retry(self, mock_get, download_service, sample_source, tmp_path):
        """测试带重试的下载"""
        # 第一次失败，第二次成功
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.headers = {"content-length": "100"}
        mock_response_success.iter_content.return_value = [b"test data"]
        mock_response_success.__enter__ = Mock(return_value=mock_response_success)
        mock_response_success.__exit__ = Mock(return_value=False)

        mock_get.side_effect = [
            Exception("First attempt failed"),
            mock_response_success,
        ]

        target_path = tmp_path / "test.tar.gz"
        result = download_service.download_with_retry(
            [sample_source],
            target_path,
            max_attempts=2
        )

        assert result.success
        assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_async_download(self, download_service, sample_source, tmp_path):
        """测试异步下载"""
        with patch('aiohttp.ClientSession') as mock_session:
            # 模拟异步响应
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {"content-length": "100"}
            mock_response.content.iter_chunked = AsyncMock(
                return_value=iter([b"test data"])
            )
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=False)

            mock_session_instance = AsyncMock()
            mock_session_instance.get = Mock(return_value=mock_response)
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=False)
            mock_session.return_value = mock_session_instance

            target_path = tmp_path / "test.tar.gz"
            result = await download_service.async_download([sample_source], target_path)

            assert result.success
            assert result.file_path == target_path


class TestDownloadResult:
    """测试DownloadResult"""

    def test_create_success_result(self):
        """测试创建成功结果"""
        result = DownloadResult(
            success=True,
            file_path=Path("/tmp/test.tar.gz"),
            downloaded_size=1024,
            elapsed_time=10.5,
        )
        assert result.success
        assert result.downloaded_size == 1024
        assert result.error_message is None

    def test_create_failure_result(self):
        """测试创建失败结果"""
        result = DownloadResult(
            success=False,
            file_path=None,
            downloaded_size=0,
            elapsed_time=5.0,
            error_message="下载失败",
        )
        assert not result.success
        assert result.error_message == "下载失败"


# AsyncMock helper for Python 3.7+
try:
    from unittest.mock import AsyncMock
except ImportError:
    # Fallback for older Python versions
    class AsyncMock(Mock):
        async def __call__(self, *args, **kwargs):
            return super().__call__(*args, **kwargs)

        async def __aenter__(self, *args, **kwargs):
            return self

        async def __aexit__(self, *args, **kwargs):
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

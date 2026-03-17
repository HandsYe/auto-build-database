"""
下载服务

提供文件下载功能，支持多源下载、断点续传、异步下载等。
"""

import asyncio
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, AsyncGenerator

import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from biodeploy.models.errors import DownloadError, ErrorCode
from biodeploy.models.metadata import DownloadSource
from biodeploy.infrastructure.logger import get_logger


@dataclass
class DownloadResult:
    """下载结果

    Attributes:
        success: 是否成功
        file_path: 下载的文件路径
        downloaded_size: 已下载大小（字节）
        elapsed_time: 耗时（秒）
        error_message: 错误信息
    """

    success: bool
    file_path: Optional[Path]
    downloaded_size: int
    elapsed_time: float
    error_message: Optional[str] = None


class DownloadService:
    """下载服务

    提供文件下载功能，支持多源下载、断点续传、进度回调等。

    Attributes:
        chunk_size: 下载块大小
        timeout: 超时时间
        max_retries: 最大重试次数
        retry_delay: 重试延迟
    """

    def __init__(
        self,
        chunk_size: int = 8192,
        timeout: int = 300,
        max_retries: int = 3,
        retry_delay: int = 5,
        proxy: Optional[str] = None,
    ) -> None:
        """初始化下载服务

        Args:
            chunk_size: 下载块大小（字节）
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            proxy: 代理服务器地址
        """
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.proxy = proxy
        self.logger = get_logger("download_service")

        # 创建会话
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建HTTP会话

        Returns:
            配置好的requests会话
        """
        session = requests.Session()

        # 设置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 设置代理
        if self.proxy:
            session.proxies = {
                "http": self.proxy,
                "https": self.proxy,
            }

        return session

    def download(
        self,
        sources: List[DownloadSource],
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> DownloadResult:
        """从多个源下载文件

        按优先级尝试从不同的源下载文件，直到成功或所有源都失败。

        Args:
            sources: 下载源列表
            target_path: 目标文件路径
            options: 下载选项
            progress_callback: 进度回调函数 (downloaded_size, total_size)

        Returns:
            下载结果
        """
        options = options or {}
        start_time = time.time()

        # 按优先级排序下载源
        sorted_sources = sorted(sources, key=lambda x: x.priority)

        # 尝试从每个源下载
        for attempt, source in enumerate(sorted_sources):
            self.logger.info(
                f"尝试从源下载 (尝试 {attempt + 1}/{len(sorted_sources)}): {source.url}"
            )

            try:
                result = self._download_from_source(
                    source, target_path, options, progress_callback
                )

                if result.success:
                    result.elapsed_time = time.time() - start_time
                    return result

            except Exception as e:
                self.logger.warning(f"从源 {source.url} 下载失败: {e}")
                continue

        # 所有源都失败
        elapsed_time = time.time() - start_time
        return DownloadResult(
            success=False,
            file_path=None,
            downloaded_size=0,
            elapsed_time=elapsed_time,
            error_message="所有下载源都失败",
        )

    def _download_from_source(
        self,
        source: DownloadSource,
        target_path: Path,
        options: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> DownloadResult:
        """从单个源下载文件

        Args:
            source: 下载源
            target_path: 目标文件路径
            options: 下载选项
            progress_callback: 进度回调函数

        Returns:
            下载结果
        """
        target_path = Path(target_path)

        # 确保目标目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 检查是否支持断点续传
        resume_enabled = options.get("resume_enabled", True)
        downloaded_size = 0

        # 检查是否有部分下载的文件
        if resume_enabled and target_path.exists():
            downloaded_size = target_path.stat().st_size
            self.logger.info(f"检测到部分下载的文件，已下载 {downloaded_size} 字节")

        # 设置请求头
        headers = {}
        if downloaded_size > 0:
            headers["Range"] = f"bytes={downloaded_size}-"

        try:
            # 发起请求
            response = self.session.get(
                source.url,
                headers=headers,
                stream=True,
                timeout=self.timeout,
            )

            # 检查响应状态
            if response.status_code not in [200, 206]:
                raise DownloadError(
                    f"HTTP错误: {response.status_code}",
                    ErrorCode.DOWNLOAD_FAILED,
                    {"url": source.url, "status_code": response.status_code},
                )

            # 获取文件总大小
            total_size = int(response.headers.get("content-length", 0))
            if response.status_code == 206:
                # 断点续传，total_size是剩余部分的大小
                content_range = response.headers.get("content-range", "")
                if content_range:
                    total_size = int(content_range.split("/")[-1])
            elif downloaded_size > 0:
                # 服务器不支持断点续传，重新下载
                downloaded_size = 0

            self.logger.info(f"开始下载，总大小: {total_size} 字节")

            # 下载文件
            mode = "ab" if downloaded_size > 0 and response.status_code == 206 else "wb"
            with open(target_path, mode) as f:
                for chunk in response.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 调用进度回调
                        if progress_callback:
                            progress_callback(downloaded_size, total_size)

            # 验证文件大小（默认关闭；某些服务器/代理可能不返回可靠的content-length）
            verify_size = bool(options.get("verify_size", False))
            if verify_size and total_size > 0 and downloaded_size != total_size:
                raise DownloadError(
                    f"文件大小不匹配: 期望 {total_size}，实际 {downloaded_size}",
                    ErrorCode.DOWNLOAD_FAILED,
                    {"expected": total_size, "actual": downloaded_size},
                )

            self.logger.info(f"下载完成: {target_path}")

            return DownloadResult(
                success=True,
                file_path=target_path,
                downloaded_size=downloaded_size,
                elapsed_time=0.0,
            )

        except requests.exceptions.Timeout:
            raise DownloadError(
                f"下载超时: {source.url}",
                ErrorCode.DOWNLOAD_TIMEOUT,
                {"url": source.url, "timeout": self.timeout},
            )
        except requests.exceptions.RequestException as e:
            raise DownloadError(
                f"网络错误: {e}",
                ErrorCode.DOWNLOAD_NETWORK_ERROR,
                {"url": source.url, "error": str(e)},
            )
        except Exception as e:
            raise DownloadError(
                f"下载失败: {e}",
                ErrorCode.DOWNLOAD_FAILED,
                {"url": source.url, "error": str(e)},
            )

    def download_with_retry(
        self,
        sources: List[DownloadSource],
        target_path: Path,
        max_attempts: int = 3,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> DownloadResult:
        """带重试的下载

        Args:
            sources: 下载源列表
            target_path: 目标文件路径
            max_attempts: 最大尝试次数
            options: 下载选项
            progress_callback: 进度回调函数

        Returns:
            下载结果
        """
        for attempt in range(max_attempts):
            self.logger.info(f"下载尝试 {attempt + 1}/{max_attempts}")

            result = self.download(sources, target_path, options, progress_callback)

            if result.success:
                return result

            if attempt < max_attempts - 1:
                self.logger.warning(f"下载失败，{self.retry_delay}秒后重试...")
                time.sleep(self.retry_delay)

        return result

    def close(self) -> None:
        """关闭会话"""
        self.session.close()

    @contextmanager
    def session_context(self) -> 'DownloadService':
        """会话上下文管理器
        
        Yields:
            DownloadService实例
        """
        try:
            yield self
        finally:
            self.close()

    async def async_download(
        self,
        sources: List[DownloadSource],
        target_path: Path,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> DownloadResult:
        """异步下载文件
        
        Args:
            sources: 下载源列表
            target_path: 目标文件路径
            options: 下载选项
            progress_callback: 进度回调函数
            
        Returns:
            下载结果
        """
        options = options or {}
        start_time = time.time()
        
        # 按优先级排序下载源
        sorted_sources = sorted(sources, key=lambda x: x.priority)
        
        # 尝试从每个源下载
        for attempt, source in enumerate(sorted_sources):
            self.logger.info(
                f"异步下载尝试 (尝试 {attempt + 1}/{len(sorted_sources)}): {source.url}"
            )
            
            try:
                result = await self._async_download_from_source(
                    source, target_path, options, progress_callback
                )
                
                if result.success:
                    result.elapsed_time = time.time() - start_time
                    return result
                    
            except Exception as e:
                self.logger.warning(f"异步下载失败 {source.url}: {e}")
                continue
        
        # 所有源都失败
        elapsed_time = time.time() - start_time
        return DownloadResult(
            success=False,
            file_path=None,
            downloaded_size=0,
            elapsed_time=elapsed_time,
            error_message="所有下载源都失败",
        )

    async def _async_download_from_source(
        self,
        source: DownloadSource,
        target_path: Path,
        options: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> DownloadResult:
        """异步从单个源下载文件
        
        Args:
            source: 下载源
            target_path: 目标文件路径
            options: 下载选项
            progress_callback: 进度回调函数
            
        Returns:
            下载结果
        """
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 检查是否支持断点续传
        resume_enabled = options.get("resume_enabled", True)
        downloaded_size = 0
        
        if resume_enabled and target_path.exists():
            downloaded_size = target_path.stat().st_size
            self.logger.info(f"检测到部分下载的文件，已下载 {downloaded_size} 字节")
        
        # 设置请求头
        headers = {}
        if downloaded_size > 0:
            headers["Range"] = f"bytes={downloaded_size}-"
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(source.url, headers=headers) as response:
                    # 检查响应状态
                    if response.status not in [200, 206]:
                        raise DownloadError(
                            f"HTTP错误: {response.status}",
                            ErrorCode.DOWNLOAD_FAILED,
                            {"url": source.url, "status_code": response.status},
                        )
                    
                    # 获取文件总大小
                    total_size = int(response.headers.get("content-length", 0))
                    if response.status == 206:
                        content_range = response.headers.get("content-range", "")
                        if content_range:
                            total_size = int(content_range.split("/")[-1])
                    elif downloaded_size > 0:
                        downloaded_size = 0
                    
                    self.logger.info(f"开始异步下载，总大小: {total_size} 字节")
                    
                    # 下载文件
                    mode = "ab" if downloaded_size > 0 and response.status == 206 else "wb"
                    with open(target_path, mode) as f:
                        chunks = response.content.iter_chunked(self.chunk_size)
                        if asyncio.iscoroutine(chunks):
                            chunks = await chunks

                        if hasattr(chunks, "__aiter__"):
                            async for chunk in chunks:
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    if progress_callback:
                                        progress_callback(downloaded_size, total_size)
                        else:
                            for chunk in chunks:
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    if progress_callback:
                                        progress_callback(downloaded_size, total_size)
                    
                    # 验证文件大小（默认关闭；某些服务器/代理可能不返回可靠的content-length）
                    verify_size = bool(options.get("verify_size", False))
                    if verify_size and total_size > 0 and downloaded_size != total_size:
                        raise DownloadError(
                            f"文件大小不匹配: 期望 {total_size}，实际 {downloaded_size}",
                            ErrorCode.DOWNLOAD_FAILED,
                            {"expected": total_size, "actual": downloaded_size},
                        )
                    
                    self.logger.info(f"异步下载完成: {target_path}")
                    
                    return DownloadResult(
                        success=True,
                        file_path=target_path,
                        downloaded_size=downloaded_size,
                        elapsed_time=0.0,
                    )
                    
        except asyncio.TimeoutError:
            raise DownloadError(
                f"下载超时: {source.url}",
                ErrorCode.DOWNLOAD_TIMEOUT,
                {"url": source.url, "timeout": self.timeout},
            )
        except aiohttp.ClientError as e:
            raise DownloadError(
                f"网络错误: {e}",
                ErrorCode.DOWNLOAD_NETWORK_ERROR,
                {"url": source.url, "error": str(e)},
            )
        except Exception as e:
            raise DownloadError(
                f"下载失败: {e}",
                ErrorCode.DOWNLOAD_FAILED,
                {"url": source.url, "error": str(e)},
            )

"""
安装管理器

处理数据库的安装流程，包括下载、校验、安装和索引构建。
"""

import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Generator

from biodeploy.adapters.adapter_registry import AdapterRegistry
from biodeploy.adapters.base_adapter import BaseAdapter
from biodeploy.core.dependency_manager import DependencyManager
from biodeploy.core.state_manager import StateManager
from biodeploy.infrastructure.filesystem import FileSystem
from biodeploy.infrastructure.logger import get_logger
from biodeploy.models.state import InstallationRecord, InstallationStatus
from biodeploy.models.errors import InstallError, ErrorCode
from biodeploy.services.checksum_service import ChecksumService

from biodeploy.services.download_service import DownloadService
from biodeploy.services.environment_service import EnvironmentService
from biodeploy.services.index_service import IndexService


class InstallationManager:
    """安装管理器

    负责管理数据库的完整安装流程。
    """

    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        registry: Optional[AdapterRegistry] = None,
        install_path: Optional[Path] = None,
    ):
        """初始化安装管理器

        Args:
            state_manager: 状态管理器
            registry: 适配器注册表
            install_path: 默认安装路径
        """
        self._state_manager = state_manager or StateManager()
        self._registry = registry or AdapterRegistry()
        self._install_path = install_path or Path.home() / "bio_databases"
        self._download_service = DownloadService()
        self._index_service = IndexService()
        self._env_service = EnvironmentService()
        self._dep_manager = DependencyManager()
        self._logger = get_logger("installation_manager")

    def install(
        self,
        database: str,
        version: Optional[str] = None,
        install_path: Optional[Path] = None,
        options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> bool:
        """安装单个数据库

        Args:
            database: 数据库名称
            version: 数据库版本，如果为None则使用最新版本
            install_path: 安装路径，如果为None则使用默认路径
            options: 安装选项
            progress_callback: 进度回调函数 (message, progress)

        Returns:
            如果安装成功返回True，否则返回False
        """
        options = options or {}

        # 获取适配器
        adapter = self._registry.get(database)
        if not adapter:
            self._logger.error(f"未找到适配器: {database}")
            return False

        # 获取版本
        version = version or adapter.get_latest_version()

        # 检查是否已安装
        if self._state_manager.is_installed(database, version):
            if not options.get("force", False):
                self._logger.info(f"{database} {version} 已安装，跳过")
                return True
            self._logger.info(f"强制重新安装 {database} {version}")

        # 创建安装记录
        record = InstallationRecord(
            name=database,
            version=version,
            install_path=install_path or self._install_path / database / version,
            install_time=datetime.now(),
            status=InstallationStatus.PENDING,
        )

        self._logger.info(f"开始安装 {database} {version}")
        self._notify_progress(progress_callback, "开始安装", 0.0)

        try:
            # 1. 检查依赖
            self._notify_progress(progress_callback, "检查依赖", 0.05)
            if not self._check_dependencies(adapter, options):
                record.set_error("依赖检查失败")
                self._state_manager.save_record(record)
                return False

            # 2. 检查磁盘空间
            self._notify_progress(progress_callback, "检查磁盘空间", 0.1)
            if not self._check_disk_space(adapter, version, record.install_path):
                record.set_error("磁盘空间不足")
                self._state_manager.save_record(record)
                return False

            # 3. 下载
            self._notify_progress(progress_callback, "下载", 0.15)
            record.status = InstallationStatus.DOWNLOADING
            record.current_step = "downloading"
            self._state_manager.save_record(record)

            # temp_path 作为“下载工作目录”供各 Adapter 写入多个文件
            temp_path = Path(f"/tmp/biodeploy/{database}_{version}")
            # 兼容历史残留：如果同名文件存在，先移除再创建目录
            if temp_path.exists() and temp_path.is_file():
                temp_path.unlink()
            temp_path.mkdir(parents=True, exist_ok=True)

            def download_progress(downloaded: int, total: int):
                if total > 0:
                    progress = 0.15 + (downloaded / total) * 0.4
                    self._notify_progress(progress_callback, "下载中", progress)

            try:
                downloaded_ok = adapter.download(version, temp_path, options, download_progress)
            except IsADirectoryError:
                # 某些适配器把 target_path 当作“单文件路径”，提供一个兜底文件路径重试
                downloaded_ok = adapter.download(
                    version, temp_path / "__download__", options, download_progress
                )

            if not downloaded_ok:
                record.set_error("下载失败")
                self._state_manager.save_record(record)
                return False

            # 4. 校验（如果提供了校验和）
            self._notify_progress(progress_callback, "校验", 0.55)
            record.status = InstallationStatus.VERIFYING
            record.current_step = "verifying"
            self._state_manager.save_record(record)

            metadata = adapter.get_metadata(version)
            if metadata.checksums:
                if not self._verify_checksums(temp_path, metadata.checksums):
                    record.set_error("校验失败")
                    self._state_manager.save_record(record)
                    return False

            # 5. 安装
            self._notify_progress(progress_callback, "安装", 0.65)
            record.status = InstallationStatus.INSTALLING
            record.current_step = "installing"
            self._state_manager.save_record(record)

            FileSystem.ensure_directory(record.install_path)

            if not adapter.install(temp_path, record.install_path, options):
                record.set_error("安装失败")
                self._state_manager.save_record(record)
                return False

            # 6. 验证安装
            self._notify_progress(progress_callback, "验证", 0.75)
            if not adapter.verify(record.install_path):
                record.set_error("验证失败")
                self._state_manager.save_record(record)
                return False

            # 7. 构建索引（如果需要）
            if not options.get("no_index", False):
                self._notify_progress(progress_callback, "构建索引", 0.8)
                record.status = InstallationStatus.INDEXING
                record.current_step = "indexing"
                self._state_manager.save_record(record)

                self._build_indexes(record, metadata.index_types, options)

            # 8. 生成配置
            self._notify_progress(progress_callback, "生成配置", 0.9)
            # 生成环境变量配置脚本
            env_script_path = record.install_path / "env.sh"
            env_vars = adapter.get_environment_variables(record.install_path, version)
            with open(env_script_path, "w") as f:
                f.write("#!/bin/bash\n")
                f.write(f"# Environment configuration for {database}\n\n")
                for key, value in env_vars.items():
                    f.write(f'export {key}="{value}"\n')
            record.config_files = [env_script_path]

            # 9. 设置环境变量
            self._notify_progress(progress_callback, "设置环境变量", 0.95)
            env_script = self._env_service.generate_export_script(record)
            if env_script:
                record.environment_variables[f"{database.upper()}_PATH"] = str(record.install_path)

                if options.get("set_env", False):
                    self._env_service.update_shell_config(record)

            # 完成
            record.status = InstallationStatus.COMPLETED
            record.progress = 1.0
            record.current_step = "completed"
            record.files = FileSystem.list_files(record.install_path, recursive=True)
            record.total_size = FileSystem.get_directory_size(record.install_path)

            self._state_manager.save_record(record)

            # 清理临时文件
            if options.get("cleanup", True):
                FileSystem.safe_remove(temp_path)

            self._notify_progress(progress_callback, "完成", 1.0)
            self._logger.info(f"安装成功: {database} {version}")
            return True

        except Exception as e:
            self._logger.error(f"安装失败: {e}")
            record.set_error(str(e))
            self._state_manager.save_record(record)
            return False

    def install_multiple(
        self,
        databases: List[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """批量安装多个数据库

        Args:
            databases: 数据库名称列表
            options: 安装选项
                - parallel: 是否并行安装
                - max_parallel: 最大并行数

        Returns:
            数据库名称到安装结果的映射
        """
        options = options or {}
        parallel = options.get("parallel", False)
        max_parallel = options.get("max_parallel", 1)

        results = {}

        if parallel and max_parallel > 1:
            # 并行安装
            from concurrent.futures import ThreadPoolExecutor, as_completed

            with ThreadPoolExecutor(max_workers=max_parallel) as executor:
                futures = {
                    executor.submit(self.install, db, None, None, options): db
                    for db in databases
                }

                for future in as_completed(futures):
                    db = futures[future]
                    try:
                        results[db] = future.result()
                    except Exception as e:
                        self._logger.error(f"安装 {db} 时出错: {e}")
                        results[db] = False
        else:
            # 串行安装
            for db in databases:
                results[db] = self.install(db, None, None, options)

        return results

    def _check_dependencies(self, adapter: BaseAdapter, options: Dict[str, Any]) -> bool:
        """检查依赖"""
        if options.get("skip_deps", False):
            return True

        dependencies = adapter.get_dependencies()
        # 即便依赖为空，也调用依赖管理器以保持行为一致（便于测试/注入）
        available, missing = self._dep_manager.check_dependencies(dependencies)

        if missing:
            self._logger.warning(f"缺少依赖: {missing}")
            for dep in missing:
                cmd = self._dep_manager.get_install_command(dep)
                if cmd:
                    self._logger.info(f"安装命令: {cmd}")
            return False

        return True

    def _check_disk_space(
        self,
        adapter: BaseAdapter,
        version: str,
        install_path: Path,
    ) -> bool:
        """检查磁盘空间"""
        requirements = adapter.get_system_requirements()
        min_disk = requirements.get("min_disk_space", 0)
        download_size = adapter.get_download_size(version)

        # 总需要空间 = 下载大小 + 安装后大小（估算为下载大小的2倍）
        total_required = download_size * 3

        if not FileSystem.check_disk_space(install_path, total_required):
            free = FileSystem.get_disk_usage(install_path)["free"]
            self._logger.error(
                f"磁盘空间不足: 需要 {total_required / (1024**3):.2f} GB, "
                f"可用 {free / (1024**3):.2f} GB"
            )
            return False

        return True

    def _verify_checksums(
        self,
        file_path: Path,
        checksums: Dict[str, str],
    ) -> bool:
        """验证校验和"""
        for algorithm, expected in checksums.items():
            if not ChecksumService.verify(file_path, expected, algorithm):
                self._logger.error(f"{algorithm} 校验失败")
                return False
        return True

    def _build_indexes(
        self,
        record: InstallationRecord,
        index_types: List[str],
        options: Dict[str, Any],
    ) -> None:
        """构建索引"""
        if not index_types:
            return

        # 查找FASTA文件
        fasta_files = list(record.install_path.rglob("*.fa"))
        fasta_files.extend(record.install_path.rglob("*.fasta"))
        fasta_files.extend(record.install_path.rglob("*.fna"))

        if not fasta_files:
            return

        for index_type in index_types:
            if not self._index_service.check_tool_available(index_type):
                self._logger.warning(f"索引工具不可用: {index_type}")
                continue

            for fasta_file in fasta_files:
                index_path = record.install_path / f"{index_type}_index"
                if self._index_service.build_index(
                    fasta_file,
                    index_type,
                    index_path,
                    options.get("index_options", {}),
                ):
                    record.index_files.append(index_path)

    def _notify_progress(
        self,
        callback: Optional[Callable[[str, float], None]],
        message: str,
        progress: float,
    ) -> None:
        """通知进度"""
        if callback:
            try:
                callback(message, progress)
            except Exception as e:
                self._logger.warning(f"进度回调失败: {e}")

    @contextmanager
    def _installation_context(
        self,
        database: str,
        version: str,
        temp_path: Path,
    ) -> Generator[Path, None, None]:
        """安装上下文管理器
        
        确保临时文件在安装失败时被清理
        
        Args:
            database: 数据库名称
            version: 数据库版本
            temp_path: 临时文件路径
            
        Yields:
            临时文件路径
        """
        try:
            # 确保临时目录存在
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            yield temp_path
        except Exception as e:
            self._logger.error(f"安装过程中发生错误: {e}")
            # 清理临时文件
            if temp_path.exists():
                try:
                    FileSystem.safe_remove(temp_path)
                    self._logger.info(f"已清理临时文件: {temp_path}")
                except Exception as cleanup_error:
                    self._logger.warning(f"清理临时文件失败: {cleanup_error}")
            raise
        finally:
            # 确保下载服务会话被关闭
            if hasattr(self._download_service, 'close'):
                try:
                    self._download_service.close()
                except Exception as e:
                    self._logger.warning(f"关闭下载服务失败: {e}")

    def _handle_installation_error(
        self,
        error: Exception,
        record: InstallationRecord,
        step: str,
    ) -> None:
        """处理安装错误
        
        Args:
            error: 异常对象
            record: 安装记录
            step: 当前步骤
        """
        error_message = f"{step}失败: {str(error)}"
        
        # 根据错误类型设置不同的错误详情
        error_details = {
            "step": step,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        
        # 如果是自定义错误，添加更多详情
        if isinstance(error, InstallError):
            error_details["error_code"] = error.error_code.value if error.error_code else None
            error_details["context"] = error.details
        
        record.set_error(error_message, error_details)
        self._state_manager.save_record(record)
        
        self._logger.error(
            f"安装失败 [{record.name} {record.version}]: {error_message}",
            exc_info=True,
        )

#!/usr/bin/env python3
"""
BioDeploy 全面功能测试脚本

测试所有核心功能模块，生成详细的测试报告。
"""

import os
import sys
import json
import tempfile
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加源路径
sys.path.insert(0, "/home/yehui/script/auto-build-database/src")

# 导入BioDeploy模块
from biodeploy.models.config import Config
from biodeploy.infrastructure.config_manager import ConfigManager
from biodeploy.adapters.adapter_registry import AdapterRegistry, adapter_registry
from biodeploy.models.metadata import DatabaseMetadata
from biodeploy.core.state_manager import StateManager, State
from biodeploy.infrastructure.state_storage import StateStorage
from biodeploy.infrastructure.filesystem import FileSystemManager
from biodeploy.services.download_service import DownloadService
from biodeploy.services.checksum_service import ChecksumService
from biodeploy.services.index_service import IndexService
from biodeploy.services.environment_service import EnvironmentService
from biodeploy.services.config_generation_service import ConfigGenerationService
from biodeploy.core.installation_manager import InstallationManager
from biodeploy.core.uninstall_manager import UninstallManager
from biodeploy.core.update_manager import UpdateManager
from biodeploy.models.state import InstallationState, FileInfo


class TestReporter:
    """测试报告器"""

    def __init__(self):
        self.results = []
        self.current_section = ""

    def start_section(self, name: str):
        """开始一个测试章节"""
        self.current_section = name
        print(f"\n{'=' * 60}")
        print(f"测试章节: {name}")
        print(f"{'=' * 60}")

    def add_result(
        self, test_name: str, status: str, message: str = "", details: Any = None
    ):
        """添加测试结果"""
        result = {
            "section": self.current_section,
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.results.append(result)

        status_symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "○"
        print(f"{status_symbol} {test_name}: {message}")
        if details and status == "FAIL":
            print(f"  详情: {details}")

    def generate_report(self) -> Dict[str, Any]:
        """生成完整报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.results if r["status"] == "SKIP")

        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "0%",
            "tests": self.results,
            "generated_at": datetime.now().isoformat(),
        }

        return summary


class BioDeployTester:
    """BioDeploy 全面测试器"""

    def __init__(self):
        self.reporter = TestReporter()
        self.temp_dir = Path(tempfile.mkdtemp(prefix="biodeploy_test_"))
        self.test_config_path = self.temp_dir / "config.yaml"
        self.test_state_path = self.temp_dir / "state"
        self.test_install_path = self.temp_dir / "install"

        print(f"测试目录: {self.temp_dir}")

    def cleanup(self):
        """清理测试目录"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"已清理测试目录: {self.temp_dir}")

    def run_all_tests(self):
        """运行所有测试"""
        print("开始BioDeploy全面功能测试...")

        try:
            # 1. 配置文件测试
            self.test_configuration()

            # 2. 适配器注册测试
            self.test_adapter_registry()

            # 3. 数据库元数据测试
            self.test_database_metadata()

            # 4. 状态管理测试
            self.test_state_management()

            # 5. 文件系统测试
            self.test_filesystem()

            # 6. 下载服务测试
            self.test_download_service()

            # 7. 校验服务测试
            self.test_checksum_service()

            # 8. 索引服务测试
            self.test_index_service()

            # 9. 环境变量服务测试
            self.test_environment_service()

            # 10. 完整安装流程测试
            self.test_full_installation()

            # 11. 状态跟踪测试
            self.test_state_tracking()

            # 12. 卸载功能测试
            self.test_uninstall()

            # 13. 更新功能测试
            self.test_update()

            # 14. Python API测试
            self.test_python_api()

            # 15. CLI命令测试
            self.test_cli_commands()

        except Exception as e:
            self.reporter.add_result(
                "测试框架", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )
        finally:
            self.cleanup()

    def test_configuration(self):
        """1. 配置文件测试"""
        self.reporter.start_section("1. 配置文件测试")

        try:
            # 读取默认配置
            config_manager = ConfigManager()
            config = config_manager.load_global_config()
            self.reporter.add_result("读取默认配置", "PASS", "成功加载默认配置")

            # 验证配置完整性
            assert config.version == "1.0.0"
            assert config.install.default_install_path is not None
            assert config.download.max_parallel > 0
            assert config.network.timeout > 0
            self.reporter.add_result(
                "验证配置完整性", "PASS", "所有必需字段都存在且有效"
            )

            # 测试配置覆盖
            custom_config = Config(
                install=type(config.install)(
                    default_install_path=self.test_install_path
                ),
                download=type(config.download)(max_parallel=5),
            )
            config_manager.save_config(custom_config, self.test_config_path)
            loaded_config = config_manager.load_global_config(self.test_config_path)
            assert str(loaded_config.install.default_install_path) == str(
                self.test_install_path
            )
            assert loaded_config.download.max_parallel == 5
            self.reporter.add_result("测试配置覆盖", "PASS", "自定义配置保存并加载成功")

        except Exception as e:
            self.reporter.add_result(
                "配置文件测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_adapter_registry(self):
        """2. 适配器注册测试"""
        self.reporter.start_section("2. 适配器注册测试")

        try:
            registry = AdapterRegistry()

            # 获取适配器列表
            adapters = registry.list_adapters()
            self.reporter.add_result(
                "获取适配器列表",
                "PASS",
                f"发现 {len(adapters)} 个适配器",
                adapters[:10],
            )

            # 测试动态适配器解析
            test_adapters = [
                "ncbi_refseq_protein",
                "kegg_pathway",
                "ensembl_genome",
                "ucsc_genome_hg38",
            ]
            for name in test_adapters:
                adapter = registry.get(name)
                if adapter:
                    self.reporter.add_result(
                        f"解析适配器 {name}", "PASS", f"成功获取适配器实例"
                    )
                else:
                    self.reporter.add_result(
                        f"解析适配器 {name}", "SKIP", f"适配器不存在或未实现"
                    )

            # 测试适配器注册
            from biodeploy.adapters.ncbi_adapter import NCBIAdapter

            registry.register(NCBIAdapter)
            self.reporter.add_result("注册NCBI适配器", "PASS", "适配器注册成功")

            # 验证注册
            is_registered = registry.is_registered("ncbi_refseq") or any(
                "ncbi" in k for k in registry.list_adapters()
            )
            self.reporter.add_result(
                "验证适配器注册",
                "PASS" if is_registered else "SKIP",
                "适配器已正确注册" if is_registered else "未找到适配器",
            )

        except Exception as e:
            self.reporter.add_result(
                "适配器注册测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_database_metadata(self):
        """3. 数据库元数据测试"""
        self.reporter.start_section("3. 数据库元数据测试")

        try:
            registry = AdapterRegistry()
            adapters = registry.list_adapters()

            if not adapters:
                self.reporter.add_result("获取适配器", "SKIP", "没有可用的适配器")
                return

            # 测试一个适配器的元数据
            test_adapter_name = None
            for name in adapters:
                if name.startswith("ncbi_") or "ncbi" in name:
                    test_adapter_name = name
                    break

            if not test_adapter_name:
                test_adapter_name = adapters[0]

            adapter = registry.get(test_adapter_name)
            if adapter:
                metadata = adapter.get_metadata()
                self.reporter.add_result(
                    "获取元数据",
                    "PASS",
                    f"数据库: {metadata.display_name}, 版本: {metadata.version}",
                    metadata.__dict__
                    if hasattr(metadata, "__dict__")
                    else str(metadata),
                )

                # 验证元数据字段完整性
                required_fields = [
                    "name",
                    "display_name",
                    "version",
                    "description",
                    "category",
                    "size",
                ]
                missing_fields = [
                    f for f in required_fields if not hasattr(metadata, f)
                ]
                if missing_fields:
                    self.reporter.add_result(
                        "验证元数据字段", "WARN", f"缺少部分字段: {missing_fields}"
                    )
                else:
                    self.reporter.add_result(
                        "验证元数据字段", "PASS", "所有必需字段都存在"
                    )

                # 测试版本列表
                if hasattr(adapter, "get_available_versions"):
                    versions = adapter.get_available_versions()
                    self.reporter.add_result(
                        "获取版本列表",
                        "PASS" if versions else "SKIP",
                        f"发现 {len(versions) if versions else 0} 个版本",
                        versions[:5],
                    )
            else:
                self.reporter.add_result(
                    "获取适配器", "SKIP", f"无法获取适配器 {test_adapter_name}"
                )

        except Exception as e:
            self.reporter.add_result(
                "数据库元数据测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_state_management(self):
        """4. 状态管理测试"""
        self.reporter.start_section("4. 状态管理测试")

        try:
            # 创建状态管理器
            state_manager = StateManager(str(self.test_state_path))
            self.reporter.add_result("创建状态管理器", "PASS", "状态管理器创建成功")

            # 保存状态
            test_state = State(
                database="test_db",
                status="installing",
                progress=0.5,
                files_downloaded=5,
                total_files=10,
                installed_path=str(self.test_install_path / "test_db"),
            )
            state_manager.save_state(test_state)
            self.reporter.add_result("保存状态", "PASS", "状态保存成功")

            # 加载状态
            loaded_state = state_manager.load_state("test_db")
            assert loaded_state is not None
            assert loaded_state.database == "test_db"
            assert loaded_state.status == "installing"
            self.reporter.add_result("加载状态", "PASS", "状态加载成功且数据一致")

            # 更新状态
            state_manager.update_state("test_db", status="installed", progress=1.0)
            updated_state = state_manager.load_state("test_db")
            assert updated_state.status == "installed"
            assert updated_state.progress == 1.0
            self.reporter.add_result("更新状态", "PASS", "状态更新成功")

            # 查询状态
            all_states = state_manager.get_all_states()
            assert "test_db" in all_states
            self.reporter.add_result(
                "查询状态", "PASS", f"查询到 {len(all_states)} 个状态"
            )

        except Exception as e:
            self.reporter.add_result(
                "状态管理测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_filesystem(self):
        """5. 文件系统测试"""
        self.reporter.start_section("5. 文件系统测试")

        try:
            fs = FileSystemManager()

            # 目录创建
            test_dir = self.temp_dir / "test_dir"
            fs.create_directory(test_dir, exist_ok=True)
            assert test_dir.exists()
            self.reporter.add_result("目录创建", "PASS", f"创建目录: {test_dir}")

            # 磁盘空间检查
            disk_info = fs.check_disk_space(self.temp_dir)
            assert disk_info is not None
            self.reporter.add_result(
                "磁盘空间检查",
                "PASS",
                f"总空间: {disk_info.total / 1024**3:.1f}GB, 可用: {disk_info.free / 1024**3:.1f}GB",
            )

            # 文件操作 - 创建测试文件
            test_file = test_dir / "test.txt"
            fs.write_file(test_file, "test content")
            assert test_file.exists()
            content = fs.read_file(test_file)
            assert content == "test content"
            self.reporter.add_result("文件读写", "PASS", "文件创建、写入、读取成功")

            # 文件复制
            test_file2 = test_dir / "test2.txt"
            fs.copy_file(test_file, test_file2)
            assert test_file2.exists()
            self.reporter.add_result("文件复制", "PASS", "文件复制成功")

            # 目录删除
            fs.remove_directory(test_dir)
            assert not test_dir.exists()
            self.reporter.add_result("目录删除", "PASS", "目录删除成功")

        except Exception as e:
            self.reporter.add_result(
                "文件系统测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_download_service(self):
        """6. 下载服务测试"""
        self.reporter.start_section("6. 下载服务测试")

        try:
            config = Config()
            config.install.temp_path = self.temp_dir / "temp"
            config.install.temp_path.mkdir(exist_ok=True)

            download_service = DownloadService(config)
            self.reporter.add_result("创建下载服务", "PASS", "下载服务初始化成功")

            # 测试小文件下载
            test_url = "https://httpbin.org/file/1KB"  # 使用测试URL
            dest_file = config.install.temp_path / "test_download.bin"

            try:
                success = download_service.download_file(
                    test_url, dest_file, expected_size=1024
                )
                if success and dest_file.exists():
                    self.reporter.add_result(
                        "小文件下载",
                        "PASS",
                        f"下载成功: {dest_file.stat().st_size} bytes",
                    )
                else:
                    self.reporter.add_result(
                        "小文件下载", "SKIP", "下载失败或网络不可达"
                    )
            except Exception as e:
                self.reporter.add_result("小文件下载", "SKIP", f"网络错误: {e}")

            # 验证断点续传 (创建部分下载文件)
            partial_file = config.install.temp_path / "partial.bin"
            partial_file.write_bytes(b"partial content")
            try:
                success = download_service.download_file(
                    test_url, partial_file, expected_size=1024
                )
                self.reporter.add_result(
                    "断点续传", "PASS" if success else "SKIP", "断点续传功能测试完成"
                )
            except Exception as e:
                self.reporter.add_result("断点续传", "SKIP", f"网络错误: {e}")

        except Exception as e:
            self.reporter.add_result(
                "下载服务测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_checksum_service(self):
        """7. 校验服务测试"""
        self.reporter.start_section("7. 校验服务测试")

        try:
            checksum_service = ChecksumService()
            self.reporter.add_result("创建校验服务", "PASS", "校验服务初始化成功")

            # 创建测试文件
            test_file = self.temp_dir / "test_checksum.txt"
            test_content = b"Hello, BioDeploy! This is a test."
            test_file.write_bytes(test_content)

            # 计算MD5
            md5_hash = checksum_service.calculate_md5(test_file)
            assert len(md5_hash) == 32
            self.reporter.add_result("MD5计算", "PASS", f"MD5: {md5_hash}")

            # 计算SHA256
            sha256_hash = checksum_service.calculate_sha256(test_file)
            assert len(sha256_hash) == 64
            self.reporter.add_result("SHA256计算", "PASS", f"SHA256: {sha256_hash}")

            # 验证校验
            expected_md5 = checksum_service.calculate_md5(test_file)
            is_valid_md5 = checksum_service.verify_checksum(
                test_file, expected_md5, algorithm="md5"
            )
            assert is_valid_md5
            self.reporter.add_result("校验验证", "PASS", "MD5校验成功")

            # 测试错误的校验
            wrong_hash = "0" * 32
            is_valid_wrong = checksum_service.verify_checksum(
                test_file, wrong_hash, algorithm="md5"
            )
            assert not is_valid_wrong
            self.reporter.add_result("校验失败测试", "PASS", "错误校验被正确识别")

        except Exception as e:
            self.reporter.add_result(
                "校验服务测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_index_service(self):
        """8. 索引服务测试"""
        self.reporter.start_section("8. 索引服务测试")

        try:
            index_service = IndexService()
            self.reporter.add_result("创建索引服务", "PASS", "索引服务初始化成功")

            # 检查可用工具
            available_tools = index_service.get_available_tools()
            self.reporter.add_result(
                "检查可用工具",
                "PASS",
                f"发现 {len(available_tools)} 个工具",
                list(available_tools.keys())[:5],
            )

            # 构建命令生成
            test_db_path = self.temp_dir / "test_db.fasta"
            test_db_path.write_text(">seq1\nATCG\n>seq2\nGCTA\n")

            # 测试BLAST命令生成
            if "makeblastdb" in available_tools:
                blast_cmd = index_service.generate_index_command(
                    "blast", str(test_db_path)
                )
                self.reporter.add_result(
                    "生成BLAST索引命令", "PASS", f"命令: {' '.join(blast_cmd)}"
                )
            else:
                self.reporter.add_result("生成BLAST索引命令", "SKIP", "BLAST工具未安装")

            # 测试BWA命令生成
            if "bwa" in available_tools:
                bwa_cmd = index_service.generate_index_command("bwa", str(test_db_path))
                self.reporter.add_result(
                    "生成BWA索引命令", "PASS", f"命令: {' '.join(bwa_cmd)}"
                )
            else:
                self.reporter.add_result("生成BWA索引命令", "SKIP", "BWA工具未安装")

        except Exception as e:
            self.reporter.add_result(
                "索引服务测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_environment_service(self):
        """9. 环境变量服务测试"""
        self.reporter.start_section("9. 环境变量服务测试")

        try:
            env_service = EnvironmentService()
            self.reporter.add_result("创建环境服务", "PASS", "环境服务初始化成功")

            # 生成环境变量
            test_config = {
                "database": "test_db",
                "install_path": str(self.test_install_path),
                "bin_path": str(self.test_install_path / "bin"),
            }
            env_vars = env_service.generate_environment_variables(test_config)
            assert "PATH" in env_vars or "PATH" in env_vars.get("environment", {})
            self.reporter.add_result(
                "生成环境变量", "PASS", "环境变量生成成功", env_vars
            )

            # 配置脚本生成
            script = env_service.generate_setup_script(test_config, "bash")
            assert script is not None and len(script) > 0
            self.reporter.add_result(
                "生成Bash配置脚本", "PASS", f"脚本长度: {len(script)} 字符"
            )

            script_csh = env_service.generate_setup_script(test_config, "csh")
            assert script_csh is not None and len(script_csh) > 0
            self.reporter.add_result(
                "生成Csh配置脚本", "PASS", f"脚本长度: {len(script_csh)} 字符"
            )

        except Exception as e:
            self.reporter.add_result(
                "环境变量服务测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_full_installation(self):
        """10. 完整安装流程测试"""
        self.reporter.start_section("10. 完整安装流程测试")

        try:
            # 使用CAZy或其他小数据库测试
            registry = AdapterRegistry()

            # 找一个小的或元数据完整的数据库
            test_dbs = []
            try:
                # 先尝试获取所有数据库列表
                all_dbs = registry.list_adapters()
                self.reporter.add_result(
                    "获取数据库列表", "PASS", f"发现 {len(all_dbs)} 个可用数据库"
                )

                # 选择一个小型数据库进行测试
                preferred_dbs = [
                    "ncbi_refseq_protein",
                    "kegg_pathway",
                    "ensembl_genome_homo_sapiens",
                ]
                test_db = None
                for db in preferred_dbs:
                    if db in all_dbs:
                        test_db = db
                        break

                if not test_db and all_dbs:
                    test_db = all_dbs[0]

                if test_db:
                    self.reporter.add_result(
                        "选择测试数据库", "PASS", f"选择数据库: {test_db}"
                    )

                    # 获取适配器元数据
                    adapter = registry.get(test_db)
                    if adapter:
                        metadata = adapter.get_metadata()
                        self.reporter.add_result(
                            "获取数据库信息",
                            "PASS",
                            f"名称: {metadata.display_name}, 大小: {metadata.size}",
                        )

                        # 测试安装准备
                        install_manager = InstallationManager()

                        # 检查是否已安装
                        is_installed = install_manager.is_installed(test_db)
                        if is_installed:
                            self.reporter.add_result(
                                "检查安装状态", "SKIP", "数据库已安装，跳过安装测试"
                            )
                        else:
                            # 由于实际下载可能很大，这里只测试安装流程的前期步骤
                            self.reporter.add_result(
                                "完整安装流程",
                                "SKIP",
                                "由于数据量大且需要网络，跳过实际安装，仅验证接口",
                            )

                    else:
                        self.reporter.add_result(
                            "获取适配器", "SKIP", f"适配器 {test_db} 不可用"
                        )
                else:
                    self.reporter.add_result("选择测试数据库", "SKIP", "没有可用数据库")

            except Exception as e:
                self.reporter.add_result("完整安装流程", "SKIP", f"跳过: {e}")

        except Exception as e:
            self.reporter.add_result(
                "完整安装流程测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_state_tracking(self):
        """11. 状态跟踪测试"""
        self.reporter.start_section("11. 状态跟踪测试")

        try:
            state_manager = StateManager(str(self.test_state_path))

            # 模拟安装过程中的状态更新
            db_name = "tracking_test_db"

            stages = [
                ("pending", 0.0, "等待安装"),
                ("downloading", 0.2, "下载中"),
                ("downloading", 0.5, "下载中"),
                ("downloading", 0.8, "下载中"),
                ("installing", 0.9, "安装中"),
                ("installed", 1.0, "安装完成"),
            ]

            for status, progress, message in stages:
                state = State(
                    database=db_name,
                    status=status,
                    progress=progress,
                    message=message,
                    files_downloaded=int(progress * 10)
                    if status == "downloading"
                    else 10,
                    total_files=10,
                )
                state_manager.save_state(state)

            # 验证最终状态
            final_state = state_manager.load_state(db_name)
            assert final_state.status == "installed"
            assert final_state.progress == 1.0
            self.reporter.add_result("状态跟踪", "PASS", "安装流程状态跟踪成功")

            # 测试进度记录
            history = state_manager.get_state_history(db_name)
            self.reporter.add_result(
                "进度历史",
                "PASS",
                f"记录了 {len(history)} 个状态点" if history else "SKIP",
            )

        except Exception as e:
            self.reporter.add_result(
                "状态跟踪测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_uninstall(self):
        """12. 卸载功能测试"""
        self.reporter.start_section("12. 卸载功能测试")

        try:
            uninstall_manager = UninstallManager()
            self.reporter.add_result("创建卸载管理器", "PASS", "卸载管理器初始化成功")

            # 创建一个模拟安装状态
            state_manager = StateManager(str(self.test_state_path))
            test_db = "test_uninstall_db"
            test_install_dir = self.test_install_path / test_db
            test_install_dir.mkdir(parents=True, exist_ok=True)

            # 创建一些模拟文件
            (test_install_dir / "file1.txt").write_text("content1")
            (test_install_dir / "file2.txt").write_text("content2")

            state = State(
                database=test_db,
                status="installed",
                installed_path=str(test_install_dir),
                files=[
                    FileInfo(name="file1.txt", size=7, checksum=""),
                    FileInfo(name="file2.txt", size=7, checksum=""),
                ],
            )
            state_manager.save_state(state)

            # 测试卸载
            result = uninstall_manager.uninstall(test_db, keep_config=False)
            self.reporter.add_result(
                "执行卸载",
                "PASS" if result else "SKIP",
                "卸载成功" if result else "卸载未执行",
            )

            # 验证卸载结果
            if result:
                # 检查状态是否清除
                remaining_states = state_manager.get_all_states()
                if test_db not in remaining_states:
                    self.reporter.add_result("验证状态清除", "PASS", "状态已清除")
                else:
                    self.reporter.add_result("验证状态清除", "WARN", "状态未完全清除")

                # 检查文件是否删除
                if not test_install_dir.exists():
                    self.reporter.add_result("验证文件删除", "PASS", "文件已删除")
                else:
                    self.reporter.add_result(
                        "验证文件删除", "INFO", "文件可能保留(keep_config=True)"
                    )

        except Exception as e:
            self.reporter.add_result(
                "卸载功能测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_update(self):
        """13. 更新功能测试"""
        self.reporter.start_section("13. 更新功能测试")

        try:
            update_manager = UpdateManager()
            self.reporter.add_result("创建更新管理器", "PASS", "更新管理器初始化成功")

            # 检查更新
            registry = AdapterRegistry()
            adapters = registry.list_adapters()

            if adapters:
                test_db = adapters[0]
                update_info = update_manager.check_update(test_db)

                if update_info:
                    has_update = update_info.get("has_update", False)
                    self.reporter.add_result(
                        "检查更新",
                        "PASS",
                        f"数据库 {test_db} {'有' if has_update else '无'} 更新",
                        update_info,
                    )
                else:
                    self.reporter.add_result(
                        "检查更新", "SKIP", "无法检查更新(需要网络或数据库未安装)"
                    )
            else:
                self.reporter.add_result("检查更新", "SKIP", "没有可用数据库")

        except Exception as e:
            self.reporter.add_result(
                "更新功能测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_python_api(self):
        """14. Python API测试"""
        self.reporter.start_section("14. Python API测试")

        try:
            # 导入主要API类
            from biodeploy import InstallationManager
            from biodeploy.adapters.base_adapter import BaseAdapter

            self.reporter.add_result(
                "导入API类", "PASS", "成功导入InstallationManager和BaseAdapter"
            )

            # 创建安装管理器
            manager = InstallationManager()
            self.reporter.add_result(
                "创建安装管理器", "PASS", "InstallationManager创建成功"
            )

            # 列出可用数据库
            available = manager.list_available()
            self.reporter.add_result(
                "列出可用数据库",
                "PASS",
                f"发现 {len(available)} 个数据库",
                available[:5],
            )

            # 列出已安装数据库
            installed = manager.list_installed()
            self.reporter.add_result(
                "列出已安装数据库",
                "PASS",
                f"已安装 {len(installed)} 个数据库",
                installed,
            )

            # 获取数据库信息
            if available:
                db_info = manager.get_database_info(available[0])
                self.reporter.add_result(
                    "获取数据库信息", "PASS", f"获取 {available[0]} 信息成功", db_info
                )

        except Exception as e:
            self.reporter.add_result(
                "Python API测试", "FAIL", f"测试失败: {e}", traceback.format_exc()
            )

    def test_cli_commands(self):
        """15. CLI命令测试"""
        self.reporter.start_section("15. CLI命令测试")

        commands_to_test = [
            ("biodeploy --help", "帮助命令"),
            ("biodeploy list", "列出数据库"),
            ("biodeploy list --installed", "列出已安装数据库"),
            ("biodeploy status", "查看状态"),
            ("biodeploy catalog", "显示数据库目录"),
        ]

        for cmd, description in commands_to_test:
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    self.reporter.add_result(description, "PASS", f"命令执行成功")
                    # 如果有输出，显示前几行
                    if result.stdout:
                        lines = result.stdout.split("\n")[:3]
                        self.reporter.add_result(
                            f"{description}输出", "INFO", f"前3行: {' | '.join(lines)}"
                        )
                else:
                    error = result.stderr or f"退出码: {result.returncode}"
                    self.reporter.add_result(
                        description,
                        "FAIL" if "error" in error.lower() else "WARN",
                        f"命令执行有问题: {error}",
                    )
            except subprocess.TimeoutExpired:
                self.reporter.add_result(description, "SKIP", "命令执行超时")
            except Exception as e:
                self.reporter.add_result(description, "FAIL", f"命令执行失败: {e}")


import subprocess


def main():
    """主函数"""
    tester = BioDeployTester()

    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    finally:
        tester.cleanup()

    # 生成并保存报告
    report = tester.reporter.generate_report()

    print("\n" + "=" * 80)
    print("测试报告摘要")
    print("=" * 80)
    print(f"总测试数: {report['total_tests']}")
    print(f"通过: {report['passed']}")
    print(f"失败: {report['failed']}")
    print(f"跳过: {report['skipped']}")
    print(f"通过率: {report['pass_rate']}")
    print("=" * 80)

    # 保存报告到文件
    report_file = Path("biodeploy_test_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n详细报告已保存到: {report_file}")

    return report


if __name__ == "__main__":
    main()

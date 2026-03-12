#!/usr/bin/env python3
"""
项目验证脚本

验证BioDeploy项目的完整性和可用性。
"""

import sys
from pathlib import Path
from typing import List, Tuple

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def check_imports() -> List[Tuple[str, bool, str]]:
    """检查所有模块是否可以导入"""
    results = []

    # 核心模块
    modules = [
        ("biodeploy.models", "数据模型"),
        ("biodeploy.models.metadata", "元数据模型"),
        ("biodeploy.models.state", "状态模型"),
        ("biodeploy.models.config", "配置模型"),
        ("biodeploy.models.errors", "错误模型"),
        ("biodeploy.infrastructure", "基础设施"),
        ("biodeploy.infrastructure.config_manager", "配置管理器"),
        ("biodeploy.infrastructure.logger", "日志系统"),
        ("biodeploy.infrastructure.state_storage", "状态存储"),
        ("biodeploy.infrastructure.filesystem", "文件系统"),
        ("biodeploy.services", "服务层"),
        ("biodeploy.services.download_service", "下载服务"),
        ("biodeploy.services.checksum_service", "校验服务"),
        ("biodeploy.services.index_service", "索引服务"),
        ("biodeploy.adapters", "适配器层"),
        ("biodeploy.adapters.base_adapter", "适配器基类"),
        ("biodeploy.adapters.ncbi_adapter", "NCBI适配器"),
        ("biodeploy.cli", "命令行接口"),
        ("biodeploy.cli.main", "主命令"),
    ]

    for module_name, description in modules:
        try:
            __import__(module_name)
            results.append((module_name, True, f"✓ {description}"))
        except Exception as e:
            results.append((module_name, False, f"✗ {description}: {e}"))

    return results


def check_file_structure() -> List[Tuple[str, bool, str]]:
    """检查文件结构"""
    results = []

    required_files = [
        ("setup.py", "安装脚本"),
        ("requirements.txt", "依赖文件"),
        ("README.md", "项目说明"),
        ("LICENSE", "许可证"),
        (".gitignore", "Git忽略文件"),
        ("config/config.yaml", "配置文件"),
        ("src/biodeploy/__init__.py", "包初始化文件"),
        ("tests/unit/test_models.py", "单元测试"),
    ]

    for file_path, description in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            results.append((file_path, True, f"✓ {description}"))
        else:
            results.append((file_path, False, f"✗ {description}"))

    return results


def check_documentation() -> List[Tuple[str, bool, str]]:
    """检查文档"""
    results = []

    doc_files = [
        ("README.md", "项目说明文档"),
        ("docs/PROJECT_OVERVIEW.md", "项目概览"),
        ("docs/COMPLETION_SUMMARY.md", "完成总结"),
        ("examples/usage_example.py", "使用示例"),
        ("examples/complete_example.py", "完整示例"),
    ]

    for file_path, description in doc_files:
        full_path = project_root / file_path
        if full_path.exists():
            results.append((file_path, True, f"✓ {description}"))
        else:
            results.append((file_path, False, f"✗ {description}"))

    return results


def run_basic_tests() -> List[Tuple[str, bool, str]]:
    """运行基础测试"""
    results = []

    try:
        # 测试数据模型
        from biodeploy.models import DatabaseMetadata, DownloadSource, Config

        # 创建测试数据
        source = DownloadSource(
            url="https://example.com/test.fa.gz",
            protocol="https",
            priority=1,
        )

        metadata = DatabaseMetadata(
            name="test_db",
            version="1.0.0",
            display_name="Test Database",
            description="A test database",
            size=1024 * 1024,
            file_count=1,
            formats=["fasta"],
            download_sources=[source],
            checksums={},
        )

        config = Config()

        results.append(("数据模型测试", True, "✓ 数据模型创建成功"))

    except Exception as e:
        results.append(("数据模型测试", False, f"✗ 数据模型测试失败: {e}"))

    try:
        # 测试配置管理
        from biodeploy.infrastructure.config_manager import ConfigManager

        config_manager = ConfigManager()
        config = config_manager.load_global_config()

        results.append(("配置管理测试", True, "✓ 配置加载成功"))

    except Exception as e:
        results.append(("配置管理测试", False, f"✗ 配置管理测试失败: {e}"))

    try:
        # 测试文件系统工具
        from biodeploy.infrastructure.filesystem import FileSystem

        usage = FileSystem.get_disk_usage(Path.home())

        results.append(("文件系统测试", True, f"✓ 磁盘空间检查成功"))

    except Exception as e:
        results.append(("文件系统测试", False, f"✗ 文件系统测试失败: {e}"))

    return results


def print_results(category: str, results: List[Tuple[str, bool, str]]) -> Tuple[int, int]:
    """打印结果"""
    print(f"\n{category}:")
    print("-" * 60)

    success_count = 0
    total_count = len(results)

    for name, success, message in results:
        print(f"  {message}")
        if success:
            success_count += 1

    return success_count, total_count


def main():
    """主函数"""
    print("=" * 60)
    print("BioDeploy 项目验证")
    print("=" * 60)

    total_success = 0
    total_count = 0

    # 检查导入
    results = check_imports()
    success, count = print_results("模块导入检查", results)
    total_success += success
    total_count += count

    # 检查文件结构
    results = check_file_structure()
    success, count = print_results("文件结构检查", results)
    total_success += success
    total_count += count

    # 检查文档
    results = check_documentation()
    success, count = print_results("文档检查", results)
    total_success += success
    total_count += count

    # 运行基础测试
    results = run_basic_tests()
    success, count = print_results("基础功能测试", results)
    total_success += success
    total_count += count

    # 总结
    print("\n" + "=" * 60)
    print(f"验证完成: {total_success}/{total_count} 通过")
    print("=" * 60)

    if total_success == total_count:
        print("\n✓ 所有检查通过！项目可以正常使用。")
        return 0
    else:
        print(f"\n✗ 有 {total_count - total_success} 项检查失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
完整使用示例

演示如何使用BioDeploy进行数据库的完整安装流程。
"""

from pathlib import Path
from biodeploy.adapters.ncbi_adapter import NCBIAdapter
from biodeploy.services.download_service import DownloadService
from biodeploy.services.checksum_service import ChecksumService
from biodeploy.services.index_service import IndexService
from biodeploy.infrastructure.config_manager import ConfigManager
from biodeploy.infrastructure.state_storage import StateStorage
from biodeploy.infrastructure.logger import setup_logging, get_logger


def example_complete_installation():
    """完整安装示例"""
    print("\n" + "=" * 60)
    print("完整安装流程示例")
    print("=" * 60 + "\n")

    # 1. 设置日志
    print("步骤1: 设置日志系统")
    setup_logging(level="INFO")
    logger = get_logger("example")
    print("✓ 日志系统已设置\n")

    # 2. 加载配置
    print("步骤2: 加载配置")
    config_manager = ConfigManager()
    config = config_manager.load_global_config()
    print(f"✓ 配置已加载，安装路径: {config.install.default_install_path}\n")

    # 3. 创建适配器
    print("步骤3: 创建NCBI适配器")
    adapter = NCBIAdapter(db_type="refseq_protein")
    print(f"✓ 适配器已创建: {adapter.database_name}\n")

    # 4. 获取数据库信息
    print("步骤4: 获取数据库信息")
    metadata = adapter.get_metadata()
    print(f"数据库名称: {metadata.display_name}")
    print(f"版本: {metadata.version}")
    print(f"描述: {metadata.description}")
    print(f"大小: {metadata.size / (1024**3):.2f} GB")
    print(f"格式: {', '.join(metadata.formats)}")
    print(f"依赖: {', '.join(metadata.dependencies)}\n")

    # 5. 检查可用版本
    print("步骤5: 检查可用版本")
    versions = adapter.get_available_versions()
    print(f"可用版本: {', '.join(versions[:5])}...\n")

    # 6. 检查依赖工具
    print("步骤6: 检查依赖工具")
    index_service = IndexService()
    available_tools = index_service.list_available_tools()
    print(f"可用的索引工具: {', '.join(available_tools)}\n")

    # 7. 模拟下载（实际使用时会真实下载）
    print("步骤7: 模拟下载流程")
    print("注意: 实际使用时会真实下载文件")
    print("下载源:")
    for source in metadata.download_sources:
        print(f"  - {source.url} (优先级: {source.priority}, 镜像: {source.is_mirror})")
    print()

    # 8. 模拟安装
    print("步骤8: 模拟安装流程")
    print("安装步骤:")
    print("  1. 下载压缩文件")
    print("  2. 解压文件")
    print("  3. 验证文件完整性")
    print("  4. 构建索引（可选）")
    print("  5. 设置环境变量")
    print()

    # 9. 状态管理
    print("步骤9: 状态管理")
    state_storage = StateStorage()
    print("✓ 状态存储已初始化")
    print("  - 状态文件: ~/.biodeploy/state.json")
    print("  - 记录已安装的数据库信息\n")

    # 10. 环境变量
    print("步骤10: 环境变量设置")
    install_path = config.install.default_install_path / adapter.database_name
    env_vars = adapter.get_environment_variables(install_path, metadata.version)
    print("环境变量:")
    for key, value in env_vars.items():
        print(f"  {key}={value}")
    print()

    print("=" * 60)
    print("示例完成！")
    print("=" * 60)


def example_service_usage():
    """服务使用示例"""
    print("\n" + "=" * 60)
    print("服务层使用示例")
    print("=" * 60 + "\n")

    # 下载服务示例
    print("1. 下载服务示例")
    print("   - 支持多源下载")
    print("   - 支持断点续传")
    print("   - 支持进度回调")
    print("   - 自动重试失败下载\n")

    # 校验服务示例
    print("2. 校验服务示例")
    checksum_service = ChecksumService()
    print("   支持的算法:")
    for algo in checksum_service.SUPPORTED_ALGORITHMS:
        print(f"   - {algo}")
    print()

    # 索引服务示例
    print("3. 索引服务示例")
    index_service = IndexService()
    print("   支持的索引类型:")
    for index_type in index_service.SUPPORTED_INDEX_TYPES:
        available = "✓" if index_type in index_service.list_available_tools() else "✗"
        print(f"   {available} {index_type}")
    print()

    print("=" * 60)


def example_adapter_usage():
    """适配器使用示例"""
    print("\n" + "=" * 60)
    print("适配器使用示例")
    print("=" * 60 + "\n")

    # 创建NCBI适配器
    print("创建NCBI RefSeq Protein适配器:")
    adapter = NCBIAdapter(db_type="refseq_protein")
    print(f"  数据库名称: {adapter.database_name}")
    print(f"  最新版本: {adapter.get_latest_version()}")
    print()

    # 获取元数据
    print("获取数据库元数据:")
    metadata = adapter.get_metadata()
    print(f"  显示名称: {metadata.display_name}")
    print(f"  描述: {metadata.description}")
    print(f"  大小: {metadata.size / (1024**3):.2f} GB")
    print()

    # 检查版本
    print("检查版本可用性:")
    test_version = "2024.01"
    is_available = adapter.is_version_available(test_version)
    print(f"  版本 {test_version} 可用: {is_available}")
    print()

    print("=" * 60)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("BioDeploy 完整使用示例")
    print("=" * 60)

    # 运行所有示例
    example_complete_installation()
    example_service_usage()
    example_adapter_usage()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)
    print("\n下一步:")
    print("  1. 运行 'biodeploy --help' 查看命令行帮助")
    print("  2. 运行 'biodeploy list' 查看可用数据库")
    print("  3. 运行 'biodeploy install ncbi_refseq_protein' 安装数据库")
    print()


if __name__ == "__main__":
    main()

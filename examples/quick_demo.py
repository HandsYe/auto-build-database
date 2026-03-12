#!/usr/bin/env python3
"""
BioDeploy 快速演示

展示BioDeploy的核心功能，不进行实际的大文件下载。
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def main():
    """主演示函数"""
    print("\n" + "=" * 60)
    print("BioDeploy 功能演示")
    print("=" * 60)

    # 1. 数据库适配器演示
    print("\n【1】数据库适配器演示")
    print("-" * 60)
    from biodeploy.adapters.ncbi_adapter import NCBIAdapter

    adapter = NCBIAdapter(db_type="refseq_protein")
    print(f"✓ 创建适配器: {adapter.database_name}")

    metadata = adapter.get_metadata()
    print(f"✓ 数据库: {metadata.display_name}")
    print(f"✓ 版本: {metadata.version}")
    print(f"✓ 大小: {metadata.size / (1024**3):.2f} GB")

    # 2. 配置管理演示
    print("\n【2】配置管理演示")
    print("-" * 60)
    from biodeploy.infrastructure.config_manager import ConfigManager

    config_manager = ConfigManager()
    config = config_manager.load_global_config()
    print(f"✓ 配置版本: {config.version}")
    print(f"✓ 安装路径: {config.install.default_install_path}")
    print(f"✓ 最大并发: {config.download.max_parallel}")

    # 3. 状态管理演示
    print("\n【3】状态管理演示")
    print("-" * 60)
    from biodeploy.infrastructure.state_storage import StateStorage
    from biodeploy.models.state import InstallationRecord, InstallationStatus
    from datetime import datetime
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "state.json"
        storage = StateStorage(state_file)

        # 创建模拟记录
        record = InstallationRecord(
            name="demo_database",
            version="1.0.0",
            install_path=Path("/tmp/demo"),
            install_time=datetime.now(),
            status=InstallationStatus.COMPLETED,
        )

        storage.update(record)
        print(f"✓ 保存状态: {record.name}")

        loaded = storage.get("demo_database")
        print(f"✓ 加载状态: {loaded.name} ({loaded.status.value})")

    # 4. 校验服务演示
    print("\n【4】校验服务演示")
    print("-" * 60)
    from biodeploy.services.checksum_service import ChecksumService

    checksum_service = ChecksumService()

    # 创建测试文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("BioDeploy test content")
        test_file = Path(f.name)

    try:
        md5 = checksum_service.calculate(test_file, "md5")
        sha256 = checksum_service.calculate(test_file, "sha256")
        print(f"✓ MD5: {md5}")
        print(f"✓ SHA256: {sha256[:32]}...")
    finally:
        test_file.unlink()

    # 5. 索引服务演示
    print("\n【5】索引服务演示")
    print("-" * 60)
    from biodeploy.services.index_service import IndexService

    index_service = IndexService()
    available_tools = index_service.list_available_tools()
    print(f"✓ 可用索引工具: {', '.join(available_tools) if available_tools else '无'}")

    # 6. 命令行接口演示
    print("\n【6】命令行接口演示")
    print("-" * 60)
    print("可用命令:")
    print("  • biodeploy --help          # 查看帮助")
    print("  • biodeploy list            # 列出数据库")
    print("  • biodeploy install <name>  # 安装数据库")
    print("  • biodeploy status          # 查看状态")
    print("  • biodeploy update <name>   # 更新数据库")
    print("  • biodeploy remove <name>   # 卸载数据库")

    # 总结
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\nBioDeploy 核心功能:")
    print("  ✓ 数据库适配器系统")
    print("  ✓ 配置管理系统")
    print("  ✓ 状态管理系统")
    print("  ✓ 文件校验服务")
    print("  ✓ 索引构建服务")
    print("  ✓ 命令行接口")
    print("\n下一步:")
    print("  1. 运行 'biodeploy --help' 查看完整命令")
    print("  2. 运行 'biodeploy list' 查看可用数据库")
    print("  3. 使用 'biodeploy install <database>' 安装数据库")
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
BioDeploy 使用示例

演示如何使用BioDeploy的Python API进行数据库管理。
"""

from pathlib import Path
from biodeploy.models import (
    DatabaseMetadata,
    DownloadSource,
    InstallationRecord,
    InstallationStatus,
    Config,
)
from biodeploy.infrastructure.config_manager import ConfigManager
from biodeploy.infrastructure.state_storage import StateStorage
from biodeploy.infrastructure.filesystem import FileSystem
from biodeploy.infrastructure.logger import setup_logging, get_logger


def example_create_database_metadata():
    """示例：创建数据库元数据"""
    print("\n=== 示例1: 创建数据库元数据 ===\n")

    # 创建下载源
    primary_source = DownloadSource(
        url="https://ftp.ncbi.nlm.nih.gov/refseq/release/complete/complete.protein.faa.gz",
        protocol="https",
        priority=1,
        is_mirror=False,
        region="US",
    )

    mirror_source = DownloadSource(
        url="https://mirrors.ustc.edu.cn/ncbi/refseq/release/complete/complete.protein.faa.gz",
        protocol="https",
        priority=2,
        is_mirror=True,
        region="CN",
    )

    # 创建数据库元数据
    metadata = DatabaseMetadata(
        name="ncbi_refseq_protein",
        version="2024.01",
        display_name="NCBI RefSeq Protein",
        description="NCBI Reference Sequence Protein Database",
        size=1024 * 1024 * 1024 * 5,  # 5GB
        file_count=1,
        formats=["fasta"],
        download_sources=[primary_source, mirror_source],
        checksums={"sha256": "abc123def456"},
        dependencies=["wget", "gunzip"],
        license="Public Domain",
        website="https://www.ncbi.nlm.nih.gov/refseq/",
        tags=["protein", "reference", "ncbi"],
        category="protein",
    )

    print(f"数据库名称: {metadata.display_name}")
    print(f"版本: {metadata.version}")
    print(f"大小: {metadata.size / (1024**3):.2f} GB")
    print(f"主要下载源: {metadata.get_primary_source().url}")
    print(f"最佳镜像: {metadata.get_best_mirror('CN').url}")

    return metadata


def example_config_management():
    """示例：配置管理"""
    print("\n=== 示例2: 配置管理 ===\n")

    # 创建配置管理器
    config_manager = ConfigManager()

    # 加载全局配置
    config = config_manager.load_global_config()

    print(f"配置版本: {config.version}")
    print(f"默认安装路径: {config.install.default_install_path}")
    print(f"最大并发数: {config.download.max_parallel}")
    print(f"日志级别: {config.log.level}")

    # 获取数据库特定配置
    db_config = config_manager.get_database_config("ncbi")
    print(f"\nNCBI配置: {db_config}")

    return config_manager


def example_state_management():
    """示例：状态管理"""
    print("\n=== 示例3: 状态管理 ===\n")

    # 创建状态存储
    state_storage = StateStorage()

    # 创建安装记录
    record = InstallationRecord(
        name="test_database",
        version="1.0.0",
        install_path=Path("/data/test_database"),
        install_time="2025-03-11T10:00:00",
        status=InstallationStatus.COMPLETED,
        files=[Path("/data/test_database/file1.fa"), Path("/data/test_database/file2.fa")],
        total_size=1024 * 1024 * 100,  # 100MB
        progress=1.0,
    )

    # 保存状态
    state_storage.update(record)
    print(f"已保存状态: {record.name}")

    # 加载状态
    loaded_record = state_storage.get("test_database")
    if loaded_record:
        print(f"加载状态: {loaded_record.name}")
        print(f"状态: {loaded_record.status.value}")
        print(f"进度: {loaded_record.progress * 100:.0f}%")

    return state_storage


def example_filesystem_operations():
    """示例：文件系统操作"""
    print("\n=== 示例4: 文件系统操作 ===\n")

    # 检查磁盘空间
    path = Path.home()
    usage = FileSystem.get_disk_usage(path)
    print(f"磁盘使用情况:")
    print(f"  总空间: {usage['total'] / (1024**3):.2f} GB")
    print(f"  已使用: {usage['used'] / (1024**3):.2f} GB")
    print(f"  可用空间: {usage['free'] / (1024**3):.2f} GB")

    # 检查权限
    if FileSystem.check_permissions(path):
        print(f"\n✓ 对 {path} 有写权限")

    # 检查磁盘空间是否足够
    required_size = 1024 * 1024 * 1024  # 1GB
    if FileSystem.check_disk_space(path, required_size):
        print(f"✓ 磁盘空间足够 (需要 {required_size / (1024**2):.0f} MB)")


def example_logging():
    """示例：日志系统"""
    print("\n=== 示例5: 日志系统 ===\n")

    # 设置日志
    setup_logging(level="DEBUG")

    # 获取日志记录器
    logger = get_logger("example")

    # 记录不同级别的日志
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")

    print("\n日志已记录到控制台和文件")


def main():
    """主函数"""
    print("=" * 60)
    print("BioDeploy 使用示例")
    print("=" * 60)

    # 运行所有示例
    example_create_database_metadata()
    example_config_management()
    example_state_management()
    example_filesystem_operations()
    example_logging()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

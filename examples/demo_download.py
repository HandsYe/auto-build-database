#!/usr/bin/env python3
"""
数据库下载演示

演示如何使用BioDeploy下载和安装数据库。
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from biodeploy.adapters.ncbi_adapter import NCBIAdapter
from biodeploy.services.download_service import DownloadService
from biodeploy.models.metadata import DownloadSource


def demo_database_download():
    """演示数据库下载流程"""
    print("\n" + "=" * 60)
    print("BioDeploy 数据库下载演示")
    print("=" * 60)

    # 1. 创建适配器
    print("\n步骤1: 创建数据库适配器")
    print("-" * 60)
    adapter = NCBIAdapter(db_type="refseq_protein")
    print(f"✓ 适配器已创建: {adapter.database_name}")

    # 2. 获取数据库信息
    print("\n步骤2: 获取数据库信息")
    print("-" * 60)
    metadata = adapter.get_metadata()
    print(f"数据库名称: {metadata.display_name}")
    print(f"版本: {metadata.version}")
    print(f"描述: {metadata.description}")
    print(f"大小: {metadata.size / (1024**3):.2f} GB")
    print(f"格式: {', '.join(metadata.formats)}")

    # 3. 查看下载源
    print("\n步骤3: 查看可用下载源")
    print("-" * 60)
    for i, source in enumerate(metadata.download_sources, 1):
        mirror_text = "镜像" if source.is_mirror else "主源"
        print(f"{i}. [{mirror_text}] {source.url}")
        print(f"   协议: {source.protocol}, 优先级: {source.priority}")

    # 4. 模拟下载流程
    print("\n步骤4: 模拟下载流程")
    print("-" * 60)
    print("注意: 实际下载需要网络连接和较长时间")
    print("这里仅演示下载流程，不实际下载大文件")

    # 创建下载服务
    download_service = DownloadService()
    print("✓ 下载服务已初始化")

    # 模拟下载选项
    options = {
        "resume_enabled": True,
        "verify_checksum": True,
    }
    print(f"✓ 下载选项: 断点续传={options['resume_enabled']}, 校验={options['verify_checksum']}")

    # 5. 演示下载小文件
    print("\n步骤5: 演示下载小文件")
    print("-" * 60)

    # 使用一个小的测试文件
    test_sources = [
        DownloadSource(
            url="https://www.google.com/robots.txt",
            protocol="https",
            priority=1,
            is_mirror=False,
        )
    ]

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "test_download.txt"

        print(f"下载URL: {test_sources[0].url}")
        print(f"目标路径: {target_path}")

        # 执行下载
        result = download_service.download(
            sources=test_sources,
            target_path=target_path,
            options=options,
        )

        if result.success:
            print(f"✓ 下载成功!")
            print(f"  文件大小: {result.downloaded_size} 字节")
            print(f"  耗时: {result.elapsed_time:.2f} 秒")
            print(f"  文件路径: {result.file_path}")

            # 读取文件内容（前100个字符）
            with open(result.file_path, 'r') as f:
                content = f.read(100)
                print(f"  文件内容预览: {content[:50]}...")
        else:
            print(f"✗ 下载失败: {result.error_message}")

    # 6. 总结
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)
    print("\n实际使用时，可以运行:")
    print("  biodeploy install ncbi_refseq_protein")
    print("\n或使用Python API:")
    print("  from biodeploy import InstallationManager")
    print("  manager = InstallationManager()")
    print("  manager.install('ncbi_refseq_protein')")
    print()


if __name__ == "__main__":
    demo_database_download()

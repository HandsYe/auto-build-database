#!/usr/bin/env python3
"""
完整功能测试脚本

测试BioDeploy的所有核心功能。
"""

import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_data_models():
    """测试数据模型"""
    print("\n" + "=" * 60)
    print("测试数据模型")
    print("=" * 60)

    try:
        from biodeploy.models import (
            DatabaseMetadata,
            DownloadSource,
            InstallationRecord,
            InstallationStatus,
            Config,
            BioDeployError,
            ErrorCode,
        )

        # 测试DownloadSource
        print("\n1. 测试DownloadSource...")
        source = DownloadSource(
            url="https://example.com/test.fa.gz",
            protocol="https",
            priority=1,
            is_mirror=False,
        )
        assert source.url == "https://example.com/test.fa.gz"
        print("   ✓ DownloadSource创建成功")

        # 测试DatabaseMetadata
        print("\n2. 测试DatabaseMetadata...")
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
        assert metadata.name == "test_db"
        assert metadata.get_primary_source() is not None
        print("   ✓ DatabaseMetadata创建成功")

        # 测试InstallationRecord
        print("\n3. 测试InstallationRecord...")
        record = InstallationRecord(
            name="test",
            version="1.0",
            install_path=Path("/tmp/test"),
            install_time="2025-03-11T10:00:00",
            status=InstallationStatus.PENDING,
        )
        assert record.name == "test"
        assert record.progress == 0.0
        record.update_progress(0.5, "测试中")
        assert record.progress == 0.5
        print("   ✓ InstallationRecord创建成功")

        # 测试Config
        print("\n4. 测试Config...")
        config = Config()
        assert config.version == "1.0.0"
        config_dict = config.to_dict()
        assert "version" in config_dict
        print("   ✓ Config创建成功")

        # 测试错误处理
        print("\n5. 测试错误处理...")
        error = BioDeployError(
            ErrorCode.UNKNOWN_ERROR,
            "测试错误",
            {"detail": "test"},
        )
        assert error.error_code == ErrorCode.UNKNOWN_ERROR
        error_dict = error.to_dict()
        assert "error_code" in error_dict
        print("   ✓ 错误处理正常")

        print("\n✅ 数据模型测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 数据模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_infrastructure():
    """测试基础设施层"""
    print("\n" + "=" * 60)
    print("测试基础设施层")
    print("=" * 60)

    try:
        from biodeploy.infrastructure import (
            ConfigManager,
            StateStorage,
            FileSystem,
        )
        from biodeploy.infrastructure.logger import setup_logging, get_logger

        # 测试日志系统
        print("\n1. 测试日志系统...")
        setup_logging(level="DEBUG")
        logger = get_logger("test")
        logger.info("测试日志信息")
        print("   ✓ 日志系统正常")

        # 测试配置管理
        print("\n2. 测试配置管理...")
        config_manager = ConfigManager()
        config = config_manager.load_global_config()
        assert config is not None
        print("   ✓ 配置管理正常")

        # 测试状态存储
        print("\n3. 测试状态存储...")
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            storage = StateStorage(state_file)

            # 创建测试记录
            from biodeploy.models import InstallationRecord, InstallationStatus
            record = InstallationRecord(
                name="test",
                version="1.0",
                install_path=Path("/tmp/test"),
                install_time="2025-03-11T10:00:00",
                status=InstallationStatus.COMPLETED,
            )

            # 保存和加载
            storage.update(record)
            loaded = storage.get("test")
            assert loaded is not None
            assert loaded.name == "test"
            print("   ✓ 状态存储正常")

        # 测试文件系统
        print("\n4. 测试文件系统工具...")
        usage = FileSystem.get_disk_usage(Path.home())
        assert "total" in usage
        assert "free" in usage
        print(f"   ✓ 磁盘空间: {usage['free'] / (1024**3):.2f} GB 可用")

        print("\n✅ 基础设施层测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 基础设施层测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_services():
    """测试服务层"""
    print("\n" + "=" * 60)
    print("测试服务层")
    print("=" * 60)

    try:
        from biodeploy.services import (
            DownloadService,
            ChecksumService,
            IndexService,
        )

        # 测试下载服务
        print("\n1. 测试下载服务...")
        download_service = DownloadService()
        assert download_service is not None
        print("   ✓ 下载服务初始化成功")

        # 测试校验服务
        print("\n2. 测试校验服务...")
        checksum_service = ChecksumService()

        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            test_file = Path(f.name)

        try:
            # 计算校验和
            md5 = checksum_service.calculate(test_file, "md5")
            sha256 = checksum_service.calculate(test_file, "sha256")
            assert md5 is not None
            assert sha256 is not None
            print(f"   ✓ MD5: {md5[:16]}...")
            print(f"   ✓ SHA256: {sha256[:16]}...")
        finally:
            test_file.unlink()

        # 测试索引服务
        print("\n3. 测试索引服务...")
        index_service = IndexService()
        available_tools = index_service.list_available_tools()
        print(f"   ✓ 可用索引工具: {', '.join(available_tools) if available_tools else '无'}")

        print("\n✅ 服务层测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 服务层测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adapters():
    """测试适配器层"""
    print("\n" + "=" * 60)
    print("测试适配器层")
    print("=" * 60)

    try:
        from biodeploy.adapters import BaseAdapter, NCBIAdapter

        # 测试NCBI适配器
        print("\n1. 测试NCBI适配器...")
        adapter = NCBIAdapter(db_type="refseq_protein")
        assert adapter.database_name == "ncbi_refseq_protein"
        print(f"   ✓ 适配器名称: {adapter.database_name}")

        # 获取元数据
        print("\n2. 测试获取元数据...")
        metadata = adapter.get_metadata()
        assert metadata.name == "ncbi_refseq_protein"
        print(f"   ✓ 数据库: {metadata.display_name}")
        print(f"   ✓ 版本: {metadata.version}")
        print(f"   ✓ 大小: {metadata.size / (1024**3):.2f} GB")

        # 获取可用版本
        print("\n3. 测试获取版本列表...")
        versions = adapter.get_available_versions()
        assert len(versions) > 0
        print(f"   ✓ 可用版本: {len(versions)} 个")
        print(f"   ✓ 最新版本: {versions[0]}")

        # 测试环境变量
        print("\n4. 测试环境变量生成...")
        env_vars = adapter.get_environment_variables(Path("/data/test"), "2024.01")
        assert len(env_vars) > 0
        for key, value in list(env_vars.items())[:3]:
            print(f"   ✓ {key}={value}")

        print("\n✅ 适配器层测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 适配器层测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli():
    """测试命令行接口"""
    print("\n" + "=" * 60)
    print("测试命令行接口")
    print("=" * 60)

    try:
        from click.testing import CliRunner
        from biodeploy.cli.main import cli

        runner = CliRunner()

        # 测试--help
        print("\n1. 测试--help...")
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'BioDeploy' in result.output
        print("   ✓ --help 命令正常")

        # 测试--version
        print("\n2. 测试--version...")
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        print("   ✓ --version 命令正常")

        # 测试list命令
        print("\n3. 测试list命令...")
        result = runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        print("   ✓ list 命令正常")

        # 测试status命令
        print("\n4. 测试status命令...")
        result = runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        print("   ✓ status 命令正常")

        print("\n✅ 命令行接口测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 命令行接口测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("BioDeploy 完整功能测试")
    print("=" * 60)

    results = {}

    # 运行所有测试
    results['数据模型'] = test_data_models()
    results['基础设施层'] = test_infrastructure()
    results['服务层'] = test_services()
    results['适配器层'] = test_adapters()
    results['命令行接口'] = test_cli()

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    total = len(results)
    passed = sum(results.values())

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！项目功能完整。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项测试失败，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

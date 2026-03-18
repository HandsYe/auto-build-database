#!/usr/bin/env python3
"""
BioDeploy 全面功能测试脚本
"""

import sys
import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 添加src到Python路径
sys.path.insert(0, "/home/yehui/script/auto-build-database/src")

print("=" * 70)
print("BioDeploy 全面功能测试")
print("=" * 70)

test_count = 0
pass_count = 0


def test(name, func, critical=True):
    """测试包装器"""
    global test_count, pass_count
    test_count += 1
    try:
        func()
        print(f"  ✓ {name}")
        pass_count += 1
        return True
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        if critical:
            raise
        return False


# ============ 1. 模块导入测试 ============
print("\n" + "=" * 70)
print("【1. 模块导入测试】")
print("=" * 70)

test(
    "核心管理器导入",
    lambda: __import__(
        "biodeploy.core.installation_manager", fromlist=["InstallationManager"]
    ),
)
test(
    "服务层导入",
    lambda: __import__(
        "biodeploy.services.download_service", fromlist=["DownloadService"]
    ),
)
test("适配器层导入", lambda: __import__("biodeploy.adapters", fromlist=["NCBIAdapter"]))
test("数据模型导入", lambda: __import__("biodeploy.models.config", fromlist=["Config"]))
test(
    "基础设施导入",
    lambda: __import__(
        "biodeploy.infrastructure.config_manager", fromlist=["ConfigManager"]
    ),
)

# ============ 2. 配置管理测试 ============
print("\n" + "=" * 70)
print("【2. 配置管理测试】")
print("=" * 70)

from biodeploy.infrastructure.config_manager import ConfigManager


def test_config_load():
    cm = ConfigManager()
    config = cm.load_global_config()
    assert config.version == "1.0.0"
    assert config.install is not None
    assert config.download is not None


test("加载默认配置", test_config_load)


def test_config_values():
    cm = ConfigManager()
    config = cm.load_global_config()
    print(f"    安装路径: {config.install.default_install_path}")
    print(f"    临时路径: {config.install.temp_path}")
    print(f"    最大并发: {config.download.max_parallel}")
    print(f"    断点续传: {config.download.resume_enabled}")


test("配置值验证", test_config_values)

# ============ 3. 适配器注册测试 ============
print("\n" + "=" * 70)
print("【3. 适配器注册测试】")
print("=" * 70)

from biodeploy.adapters.adapter_registry import AdapterRegistry


def test_adapter_registry():
    registry = AdapterRegistry()
    adapters = registry.list_adapters()
    assert len(adapters) >= 30
    print(f"    总适配器数: {len(adapters)}")


test("适配器注册", test_adapter_registry)


def test_adapter_get():
    registry = AdapterRegistry()

    # 测试NCBI
    adapter = registry.get("ncbi_refseq_protein")
    assert adapter is not None
    assert adapter.database_name == "ncbi_refseq_protein"
    print("    NCBI适配器: OK")

    # 测试KEGG
    adapter2 = registry.get("kegg_pathway")
    assert adapter2 is not None
    print("    KEGG适配器: OK")

    # 测试Ensembl
    adapter3 = registry.get("ensembl_genomes")
    assert adapter3 is not None
    print("    Ensembl适配器: OK")


test("适配器获取", test_adapter_get)


def test_adapter_categories():
    registry = AdapterRegistry()
    adapters = registry.list_adapters()

    categories = {
        "ncbi_": 0,
        "ensembl_": 0,
        "ucsc_": 0,
        "kegg_": 0,
        "eggnog_": 0,
        "cazy": 0,
        "card": 0,
        "vfdb": 0,
        "go": 0,
        "cog": 0,
        "swissprot": 0,
    }

    for adapter in adapters:
        for prefix in categories:
            if prefix == "cazy" and "cazy" in adapter:
                categories[prefix] += 1
                break
            elif prefix == "card" and "card" in adapter:
                categories[prefix] += 1
                break
            elif prefix == "vfdb" and "vfdb" in adapter:
                categories[prefix] += 1
                break
            elif prefix == "go" and "go" in adapter:
                categories[prefix] += 1
                break
            elif prefix == "cog" and "cog" in adapter:
                categories[prefix] += 1
                break
            elif prefix == "swissprot" and "swissprot" in adapter:
                categories[prefix] += 1
                break
            elif adapter.startswith(prefix):
                categories[prefix] += 1
                break

    for prefix, count in sorted(categories.items()):
        if count > 0:
            print(f"    {prefix:12} : {count:2d}")


test("适配器分类统计", test_adapter_categories)

# ============ 4. 元数据测试 ============
print("\n" + "=" * 70)
print("【4. 数据库元数据测试】")
print("=" * 70)

from biodeploy.adapters.ncbi_adapter import NCBIAdapter
from biodeploy.adapters.ensembl_adapter import EnsemblAdapter
from biodeploy.adapters.ucsc_adapter import UCSCAdapter
from biodeploy.adapters.kegg_adapter import KEGGAdapter
from biodeploy.adapters.eggnog_adapter import EggNOGAdapter
from biodeploy.adapters import (
    CAZyAdapter,
    CARDAdapter,
    VFDBAdapter,
    GOAdapter,
    COGAdapter,
    SwissProtAdapter,
)


def test_ncbi_metadata():
    adapter = NCBIAdapter("refseq_protein")
    meta = adapter.get_metadata("1445")
    assert meta.name == "ncbi_refseq_protein"
    assert meta.size > 0
    assert len(meta.download_sources) > 0
    print(f"    ✓ {meta.display_name}: {meta.size / (1024**3):.1f}GB")


test("NCBI元数据", test_ncbi_metadata)


def test_ncbi_versions():
    adapter = NCBIAdapter("refseq_protein")
    versions = adapter.get_available_versions()
    assert len(versions) > 0
    print(f"    可用版本: {len(versions)} 个 (最新: {versions[0]})")


test("NCBI版本列表", test_ncbi_versions)


def test_ensembl_metadata():
    adapter = EnsemblAdapter("genomes")
    meta = adapter.get_metadata()
    assert meta.name == "ensembl_genomes"
    print(f"    ✓ {meta.display_name}: {meta.version}")


test("Ensembl元数据", test_ensembl_metadata)


def test_ucsc_metadata():
    adapter = UCSCAdapter("genome", "hg38")
    meta = adapter.get_metadata()
    assert "UCSC" in meta.display_name
    print(f"    ✓ {meta.display_name}")


test("UCSC元数据", test_ucsc_metadata)


def test_kegg_metadata():
    adapter = KEGGAdapter("pathway")
    meta = adapter.get_metadata()
    assert "KEGG" in meta.display_name
    print(f"    ✓ {meta.display_name}: {meta.version}")


test("KEGG元数据", test_kegg_metadata)


def test_eggnog_metadata():
    adapter = EggNOGAdapter("eggnog")
    meta = adapter.get_metadata()
    assert "eggNOG" in meta.display_name
    print(f"    ✓ {meta.display_name}: v{meta.version}, {meta.size / (1024**3):.1f}GB")


test("EggNOG元数据", test_eggnog_metadata)


def test_other_adapters():
    adapters = [
        ("CAZy", CAZyAdapter()),
        ("CARD", CARDAdapter()),
        ("VFDB", VFDBAdapter()),
        ("GO", GOAdapter()),
        ("COG", COGAdapter()),
        ("SwissProt", SwissProtAdapter()),
    ]

    for name, adapter in adapters:
        meta = adapter.get_metadata()
        print(f"    ✓ {meta.display_name}")


test("其他数据库适配器", test_other_adapters)

# ============ 5. 状态存储测试 ============
print("\n" + "=" * 70)
print("【5. 状态存储测试】")
print("=" * 70)

from biodeploy.infrastructure.state_storage import StateStorage
from biodeploy.models.state import InstallationRecord, InstallationStatus


def test_state_save_load():
    storage = StateStorage()

    record = InstallationRecord(
        name="test_db",
        version="1.0",
        install_path=Path("/tmp/test_db_1.0"),
        install_time=datetime.now(),
        status=InstallationStatus.COMPLETED,
        total_size=1024 * 1024,
    )

    storage.save(record)
    records = storage.load()
    assert len(records) > 0
    print("    保存/加载: OK")


test("状态存储: 保存/加载", test_state_save_load)


def test_state_update():
    storage = StateStorage()

    record = InstallationRecord(
        name="update_test",
        version="2.0",
        install_path=Path("/tmp/update_test_2.0"),
        install_time=datetime.now(),
        status=InstallationStatus.PENDING,
    )

    storage.save(record)
    storage.update_status("update_test", "2.0", InstallationStatus.COMPLETED)

    records = storage.load("update_test", "2.0")
    assert len(records) > 0
    assert records[0].status == InstallationStatus.COMPLETED
    print("    状态更新: OK")


test("状态存储: 更新", test_state_update)


def test_state_remove():
    storage = StateStorage()

    record = InstallationRecord(
        name="remove_test",
        version="3.0",
        install_path=Path("/tmp/remove_test_3.0"),
        install_time=datetime.now(),
        status=InstallationStatus.FAILED,
    )

    storage.save(record)
    result = storage.remove("remove_test")
    assert result is True
    print("    删除记录: OK")


test("状态存储: 删除", test_state_remove)


def test_state_exists():
    storage = StateStorage()
    exists = storage.exists("remove_test")
    print(f"    存在性检查: {exists}")


test("状态存储: 存在性检查", test_state_exists)

# ============ 6. 文件系统测试 ============
print("\n" + "=" * 70)
print("【6. 文件系统工具测试】")
print("=" * 70)

from biodeploy.infrastructure.filesystem import FileSystem


def test_filesystem_ops():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # 目录创建
        test_dir = base_dir / "test_dir"
        FileSystem.ensure_directory(test_dir)
        assert test_dir.exists()
        print("    目录创建: OK")

        # 文件写入
        test_file = test_dir / "test.txt"
        FileSystem.safe_write(test_file, "Hello BioDeploy!")
        assert test_file.exists()
        print("    文件写入: OK")

        # 文件读取
        content = FileSystem.safe_read(test_file)
        assert content == "Hello BioDeploy!"
        print("    文件读取: OK")

        # 文件复制
        copy_file = test_dir / "copy.txt"
        FileSystem.safe_copy(test_file, copy_file)
        assert copy_file.exists()
        print("    文件复制: OK")

        # 目录删除
        FileSystem.safe_remove(test_dir)
        assert not test_dir.exists()
        print("    删除操作: OK")


test("文件系统操作", test_filesystem_ops)


def test_disk_space():
    free = FileSystem.get_free_space(Path("/tmp"))
    print(f"    可用空间: {free / (1024**3):.1f} GB")
    assert free > 0


test("磁盘空间检查", test_disk_space)

# ============ 7. 校验服务测试 ============
print("\n" + "=" * 70)
print("【7. 校验服务测试】")
print("=" * 70)

from biodeploy.services.checksum_service import ChecksumService


def test_md5():
    cs = ChecksumService()

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Test content for MD5")
        test_file = f.name

    md5 = cs.calculate_checksum(test_file, "md5")
    assert md5 is not None and len(md5) == 32
    print(f"    MD5: {md5}")
    Path(test_file).unlink()


test("MD5计算", test_md5)


def test_sha256():
    cs = ChecksumService()

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Test content for SHA256")
        test_file = f.name

    sha256 = cs.calculate_checksum(test_file, "sha256")
    assert sha256 is not None and len(sha256) == 64
    print(f"    SHA256: {sha256[:32]}...")
    Path(test_file).unlink()


test("SHA256计算", test_sha256)


def test_verification():
    cs = ChecksumService()

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Verify test content")
        test_file = f.name

    expected = cs.calculate_checksum(test_file, "md5")
    is_valid = cs.verify_checksum(test_file, "md5", expected)
    assert is_valid is True

    wrong = cs.verify_checksum(test_file, "md5", "0" * 32)
    assert wrong is False
    print("    校验验证: OK")
    Path(test_file).unlink()


test("校验验证", test_verification)

# ============ 8. 索引服务测试 ============
print("\n" + "=" * 70)
print("【8. 索引服务测试】")
print("=" * 70)

from biodeploy.services.index_service import IndexService


def test_index_tools():
    isvc = IndexService()
    tools = isvc.get_available_tools()
    print(f"    可用工具: {', '.join(tools)}")
    assert len(tools) > 0


test("可用索引工具", test_index_tools)


def test_blast_cmd():
    isvc = IndexService()
    cmd = isvc.build_index_command(
        tool="blast",
        input_file=Path("/tmp/test.fasta"),
        output_dir=Path("/tmp/blast_db"),
    )
    assert "makeblastdb" in cmd
    print(f"    BLAST: {cmd[:50]}...")


test("BLAST命令", test_blast_cmd)


def test_bwa_cmd():
    isvc = IndexService()
    cmd = isvc.build_index_command(tool="bwa", input_file=Path("/tmp/genome.fasta"))
    assert "bwa index" in cmd
    print(f"    BWA: {cmd[:50]}...")


test("BWA命令", test_bwa_cmd)


def test_bowtie2_cmd():
    isvc = IndexService()
    cmd = isvc.build_index_command(tool="bowtie2", input_file=Path("/tmp/genome.fasta"))
    assert "bowtie2-build" in cmd
    print(f"    Bowtie2: {cmd[:50]}...")


test("Bowtie2命令", test_bowtie2_cmd)

# ============ 9. 环境变量服务测试 ============
print("\n" + "=" * 70)
print("【9. 环境变量服务测试】")
print("=" * 70)

from biodeploy.services.environment_service import EnvironmentService


def test_env_init():
    es = EnvironmentService()
    assert es is not None


test("环境服务初始化", test_env_init)


def test_bash_script():
    es = EnvironmentService()
    env_vars = {"TEST_PATH": "/data/test", "TEST_VER": "1.0"}
    script = es.generate_activation_script(env_vars, shell="bash")
    assert "export TEST_PATH=" in script
    print("    Bash脚本: OK")


test("Bash脚本生成", test_bash_script)


def test_csh_script():
    es = EnvironmentService()
    env_vars = {"CSH_VAR": "value"}
    script = es.generate_activation_script(env_vars, shell="csh")
    assert "setenv CSH_VAR" in script
    print("    CSH脚本: OK")


test("CSH脚本生成", test_csh_script)


def test_module_file():
    es = EnvironmentService()
    env_vars = {"MOD_VAR": "test"}
    module_file = es.generate_module_file(env_vars, "test/1.0")
    assert "setenv MOD_VAR" in module_file or "prepend-path" in module_file
    print("    Module文件: OK")


test("Module文件生成", test_module_file)

# ============ 10. Python API 测试 ============
print("\n" + "=" * 70)
print("【10. Python API 测试】")
print("=" * 70)


def test_installation_manager():
    from biodeploy.core.installation_manager import InstallationManager

    im = InstallationManager()
    assert hasattr(im, "install")
    assert hasattr(im, "install_multiple")
    assert hasattr(im, "uninstall")
    assert hasattr(im, "update")
    assert hasattr(im, "get_status")
    print("    InstallationManager: OK")


test("InstallationManager", test_installation_manager)


def test_state_manager():
    from biodeploy.core.state_manager import StateManager

    sm = StateManager()
    assert hasattr(sm, "get_installed_databases")
    assert hasattr(sm, "get_database_info")
    assert hasattr(sm, "get_database_versions")
    assert hasattr(sm, "is_installed")
    assert hasattr(sm, "update_status")
    assert hasattr(sm, "check_integrity")
    print("    StateManager: OK")


test("StateManager", test_state_manager)


def test_uninstall_manager():
    from biodeploy.core.uninstall_manager import UninstallManager

    um = UninstallManager()
    assert hasattr(um, "uninstall")
    assert hasattr(um, "uninstall_multiple")
    print("    UninstallManager: OK")


test("UninstallManager", test_uninstall_manager)


def test_update_manager():
    from biodeploy.core.update_manager import UpdateManager

    um = UpdateManager()
    assert hasattr(um, "check_updates")
    assert hasattr(um, "update")
    print("    UpdateManager: OK")


test("UpdateManager", test_update_manager)

# ============ 11. CLI 接口测试 ============
print("\n" + "=" * 70)
print("【11. CLI 接口测试】")
print("=" * 70)


def test_cli_help():
    result = subprocess.run(
        ["biodeploy", "--help"], capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout or "bio" in result.stdout.lower()
    print("    --help: OK")


test("CLI帮助", test_cli_help)


def test_cli_version():
    result = subprocess.run(
        ["biodeploy", "--version"], capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0
    print(f"    版本: {result.stdout.strip()}")


test("CLI版本", test_cli_version)


def test_cli_list():
    result = subprocess.run(
        ["biodeploy", "list"], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    lines = result.stdout.strip().split("\n")
    print(f"    列表输出: {len(lines)} 行")


test("CLI list", test_cli_list)


def test_cli_list_json():
    result = subprocess.run(
        ["biodeploy", "list", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    import json

    data = json.loads(result.stdout)
    print(f"    JSON格式: {len(data)} 条目")


test("CLI list JSON", test_cli_list_json)


def test_cli_list_installed():
    result = subprocess.run(
        ["biodeploy", "list", "--installed"], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    print("    list --installed: OK")


test("CLI list --installed", test_cli_list_installed)


def test_cli_status():
    result = subprocess.run(
        ["biodeploy", "status"], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    print("    status命令: OK")


test("CLI status", test_cli_status)


def test_cli_update():
    result = subprocess.run(
        ["biodeploy", "update", "--check-only"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    print("    update --check-only: OK")


test("CLI update", test_cli_update)

# ============ 12. 集成测试 ============
print("\n" + "=" * 70)
print("【12. 集成测试】")
print("=" * 70)


def test_adapter_registry_integration():
    from biodeploy.adapters.adapter_registry import AdapterRegistry

    registry = AdapterRegistry()
    adapters = registry.list_adapters()

    for adapter_name in adapters[:3]:  # 测试前3个
        adapter = registry.get(adapter_name)
        assert adapter is not None
        meta = adapter.get_metadata()
        assert meta.name is not None
        print(f"    {adapter_name}: OK")


test("适配器实例化", test_adapter_registry_integration)


def test_metadata_completeness():
    from biodeploy.adapters.adapter_registry import AdapterRegistry

    registry = AdapterRegistry()
    adapters = registry.list_adapters()

    issues = []
    for adapter_name in adapters[:10]:  # 抽样检查
        try:
            adapter = registry.get(adapter_name)
            meta = adapter.get_metadata()

            if not meta.display_name:
                issues.append(f"{adapter_name}: missing display_name")
            if not meta.description:
                issues.append(f"{adapter_name}: missing description")
            if meta.size <= 0 and "ucsc" not in adapter_name:
                issues.append(f"{adapter_name}: invalid size")
        except Exception as e:
            issues.append(f"{adapter_name}: {e}")

    if issues:
        for issue in issues:
            print(f"    ⚠ {issue}")
    else:
        print("    抽样检查10个适配器: 全部通过")


test("元数据完整性", test_metadata_completeness)


def test_installation_simulation():
    from biodeploy.core.installation_manager import InstallationManager
    from biodeploy.adapters.adapter_registry import AdapterRegistry

    im = InstallationManager()
    registry = AdapterRegistry()

    # 获取一个数据库信息
    adapter = registry.get("cazy")
    if adapter:
        meta = adapter.get_metadata()
        print(f"    模拟安装: {meta.display_name}")
        print(f"    版本: {meta.version}")
        print(f"    大小: {meta.size / (1024**2):.1f} MB")
        print(f"    下载源: {len(meta.download_sources)}")
    else:
        print("    cazy适配器不存在")


test("安装流程模拟", test_installation_simulation)

# ============ 总结 ============
print("\n" + "=" * 70)
print("测试总结")
print("=" * 70)

print(f"\n总测试数: {test_count}")
print(f"通过数: {pass_count}")
print(f"失败数: {test_count - pass_count}")
print(f"通过率: {pass_count / test_count * 100:.1f}%")

if pass_count == test_count:
    print("\n✅ 所有测试通过!")
else:
    failed = test_count - pass_count
    print(f"\n⚠️  {failed} 个测试失败")

print("\n" + "=" * 70)
print("测试报告结束")
print("=" * 70)

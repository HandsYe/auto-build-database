"""
Smoke-test 命令

用于快速验证：CLI -> 列表 -> 下载/安装 -> 状态查询 是否能跑通。
默认只做本地自检；加 --download 才会进行实际下载与安装。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from biodeploy.core.installation_manager import InstallationManager
from biodeploy.infrastructure.filesystem import FileSystem


@click.command(name="smoke-test")
@click.option(
    "--database",
    "-d",
    default="go",
    show_default=True,
    help="用于实际安装验证的数据库名称（建议选择体量小的，如 go/cog）",
)
@click.option(
    "--path",
    "-p",
    type=click.Path(),
    help="安装路径（默认使用全局配置 default_install_path）",
)
@click.option(
    "--download",
    is_flag=True,
    help="执行真实下载与安装（不加则只做本地自检）",
)
@click.option(
    "--keep",
    is_flag=True,
    help="保留安装产物（默认 smoke-test 成功后会清理安装目录）",
)
@click.pass_context
def smoke_test_cmd(
    ctx: click.Context,
    database: str,
    path: Optional[str],
    download: bool,
    keep: bool,
) -> None:
    """快速验证 BioDeploy 是否可用（推荐新环境先跑一次）"""
    config = ctx.obj["config"]

    install_root = Path(path) if path else Path(config.install.default_install_path)
    click.echo("BioDeploy smoke-test")
    click.echo(f"- install_root: {install_root}")
    click.echo(f"- database: {database}")
    click.echo(f"- download: {download}")

    # 1) 本地自检：目录可写、磁盘空间信息可取
    try:
        FileSystem.ensure_directory(install_root)
        usage = FileSystem.get_disk_usage(install_root)
        click.echo(f"- disk_free: {usage.get('free', 0) / (1024**3):.2f} GB")
    except Exception as e:
        click.secho(f"✗ 本地自检失败: {e}", fg="red", err=True)
        ctx.exit(1)

    if not download:
        click.secho("✓ 本地自检通过（如需验证下载/安装链路，请加 --download）", fg="green")
        return

    # 2) 真实安装验证：建议跳过依赖检查与索引构建，减少环境差异
    manager = InstallationManager(install_path=install_root)
    options = {
        "force": True,
        "skip_deps": True,
        "no_index": True,
        "set_env": False,
        "cleanup": True,
    }

    click.echo("\n开始安装（smoke-test 模式）...")
    ok = manager.install(database=database, version=None, install_path=None, options=options)

    if not ok:
        click.secho("✗ 安装失败（smoke-test）", fg="red", err=True)
        ctx.exit(1)

    click.secho("✓ 安装成功（smoke-test）", fg="green")
    click.echo("\n状态验证：")

    # 3) 复用 status 命令输出，确保用户看到一致格式
    from biodeploy.cli.status_cmd import status as status_cmd

    ctx.invoke(status_cmd, database=database, detail=True, is_json=False)

    # 4) 可选清理（仅清理 smoke-test 这个数据库的安装目录）
    if keep:
        click.echo("\n--keep 已启用：保留安装产物")
        return

    try:
        from biodeploy.core.state_manager import StateManager

        state = StateManager()
        record = state.get_database_info(database)
        if record and record.install_path:
            FileSystem.safe_remove(Path(record.install_path))
        click.echo("\n已清理 smoke-test 安装目录（可用 --keep 保留）")
    except Exception:
        # 清理失败不影响 smoke-test 成功结论
        pass


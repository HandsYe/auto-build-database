"""
更新命令

处理数据库更新相关的命令行操作。
"""

from typing import Optional

import click

from biodeploy.core.update_manager import UpdateManager
from biodeploy.infrastructure.logger import logger


@click.command(name="update")
@click.argument("databases", nargs=-1)
@click.option(
    "--check-only",
    is_flag=True,
    help="仅检查更新，不实际更新",
)
@click.option(
    "--keep-old",
    is_flag=True,
    help="保留旧版本",
)
@click.option(
    "--parallel",
    "-j",
    type=int,
    default=1,
    help="并发更新数量",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="强制更新",
)
@click.pass_context
def update(
    ctx: click.Context,
    databases: tuple,
    check_only: bool,
    keep_old: bool,
    parallel: int,
    force: bool,
) -> None:
    """更新已安装的数据库

    DATABASES 是要更新的数据库名称列表。如果不指定，则更新所有可更新的数据库。

    示例:
        biodeploy update --check-only
        biodeploy update ncbi
        biodeploy update ncbi ensembl --keep-old
        biodeploy update --parallel 2
    """
    log = logger.get_logger("cli.update")
    manager = UpdateManager()

    # 构建选项
    options = {
        "keep_old": keep_old,
        "force": force,
        "parallel": parallel > 1,
        "max_parallel": parallel,
    }

    # 检查更新
    if not databases:
        click.echo("检查所有已安装数据库的更新...")
        updates = manager.check_updates()
    else:
        click.echo(f"检查 {len(databases)} 个数据库的更新...")
        updates = []
        for db_name in databases:
            update_info = manager.check_update(db_name)
            if update_info:
                updates.append(update_info)

    # 显示检查结果
    if check_only or not updates:
        if not updates:
            click.secho("所有数据库都是最新版本", fg="green")
            return

        click.echo()
        click.echo("可用的更新:")
        click.echo(f"{'数据库':<20} {'当前版本':<15} {'最新版本':<15} {'大小':<10}")
        click.echo("-" * 65)

        for update in updates:
            size_str = _format_size(update.download_size)
            click.echo(
                f"{update.name:<20} {update.current_version:<15} "
                f"{update.latest_version:<15} {size_str:<10}"
            )

        if check_only:
            return

    # 执行更新
    click.echo()
    click.echo(f"开始更新 {len(updates)} 个数据库...")
    click.echo()

    results = {}
    for update in updates:
        click.echo(f"更新 {update.name}: {update.current_version} -> {update.latest_version}")
        success = manager.update(update.name, options)
        results[update.name] = success

        if success:
            click.secho(f"  ✓ 更新成功", fg="green")
        else:
            click.secho(f"  ✗ 更新失败", fg="red")

    # 显示结果
    success_count = sum(1 for r in results.values() if r)
    failed_count = len(results) - success_count

    click.echo()
    click.echo(f"更新完成: 成功 {success_count}, 失败 {failed_count}")

    if failed_count > 0:
        ctx.exit(1)


def _format_size(size: int) -> str:
    """格式化文件大小"""
    if size == 0:
        return "Unknown"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

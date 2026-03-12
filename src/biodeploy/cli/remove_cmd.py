"""
移除命令

卸载已安装的数据库。
"""

from typing import Optional

import click

from biodeploy.core.uninstall_manager import UninstallManager


@click.command(name="remove")
@click.argument("databases", nargs=-1, required=True)
@click.option(
    "--version",
    "-v",
    help="指定要移除的版本",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="强制卸载，不提示确认",
)
@click.option(
    "--keep-config",
    is_flag=True,
    help="保留配置文件",
)
@click.pass_context
def remove(
    ctx: click.Context,
    databases: tuple,
    version: Optional[str],
    force: bool,
    keep_config: bool,
) -> None:
    """卸载一个或多个数据库

    DATABASES 是要卸载的数据库名称列表。

    示例:
        biodeploy remove ncbi
        biodeploy remove ncbi --version 2024.01
        biodeploy remove ncbi ensembl --force
    """
    manager = UninstallManager()

    options = {
        "keep_config": keep_config,
        "force": force,
    }

    # 确认卸载
    if not force:
        db_list = ", ".join(databases)
        version_str = f" (版本: {version})" if version else ""
        click.confirm(
            f"确定要卸载 {db_list}{version_str} 吗?",
            abort=True,
        )

    # 卸载数据库
    results = manager.uninstall_multiple(list(databases), options)

    # 显示结果
    click.echo()
    click.echo("卸载结果:")
    for db_name, success in results.items():
        if success:
            click.secho(f"  ✓ {db_name} 已卸载", fg="green")
        else:
            click.secho(f"  ✗ {db_name} 卸载失败", fg="red")

    # 检查是否有失败
    failed_count = sum(1 for r in results.values() if not r)
    if failed_count > 0:
        ctx.exit(1)

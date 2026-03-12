"""
状态命令

显示数据库的详细状态信息。
"""

from typing import Optional

import click

from biodeploy.adapters.adapter_registry import AdapterRegistry
from biodeploy.core.state_manager import StateManager


@click.command(name="status")
@click.argument("database", required=False)
@click.option(
    "--detail",
    "-d",
    is_flag=True,
    help="显示详细信息",
)
@click.option(
    "--json",
    "is_json",
    is_flag=True,
    help="以JSON格式输出",
)
@click.pass_context
def status(
    ctx: click.Context,
    database: Optional[str],
    detail: bool,
    is_json: bool,
) -> None:
    """显示数据库状态

    DATABASE 是数据库名称。如果不指定，则显示所有数据库的摘要。

    示例:
        biodeploy status
        biodeploy status ncbi
        biodeploy status ncbi --detail
        biodeploy status --json
    """
    state_manager = StateManager()
    registry = AdapterRegistry()

    if database:
        # 显示单个数据库状态
        record = state_manager.get_database_info(database)

        if not record:
            click.echo(f"数据库未安装: {database}")
            ctx.exit(1)

        if is_json:
            import json
            click.echo(json.dumps(record.to_dict(), indent=2, ensure_ascii=False))
            return

        # 显示状态
        click.echo(f"数据库: {record.name}")
        click.echo(f"版本: {record.version}")

        status_colors = {
            "completed": "green",
            "failed": "red",
            "downloading": "yellow",
            "installing": "yellow",
            "indexing": "yellow",
        }
        status_color = status_colors.get(record.status.value, "white")
        click.secho(f"状态: {record.status.value}", fg=status_color)

        click.echo(f"安装路径: {record.install_path}")
        click.echo(f"安装时间: {record.install_time}")
        click.echo(f"总大小: {_format_size(record.total_size)}")

        if detail:
            click.echo()
            click.echo("文件列表:")
            for file_path in record.files[:20]:  # 最多显示20个文件
                click.echo(f"  {file_path}")
            if len(record.files) > 20:
                click.echo(f"  ... 还有 {len(record.files) - 20} 个文件")

            if record.index_files:
                click.echo()
                click.echo("索引文件:")
                for index_path in record.index_files:
                    click.echo(f"  {index_path}")

            if record.environment_variables:
                click.echo()
                click.echo("环境变量:")
                for key, value in record.environment_variables.items():
                    click.echo(f"  {key}={value}")

        if record.error_message:
            click.echo()
            click.secho(f"错误: {record.error_message}", fg="red")

    else:
        # 显示所有数据库摘要
        summary = state_manager.get_status_summary()

        if is_json:
            import json
            click.echo(json.dumps(summary, indent=2, ensure_ascii=False))
            return

        click.echo("数据库状态摘要")
        click.echo()
        click.echo(f"总数据库数: {summary['total']}")
        click.secho(f"已安装: {summary['completed']}", fg="green")
        click.secho(f"安装中: {summary['in_progress']}", fg="yellow")
        click.secho(f"失败: {summary['failed']}", fg="red")

        if summary['databases']:
            click.echo()
            click.echo("数据库列表:")
            for name in summary['databases']:
                click.echo(f"  - {name}")


def _format_size(size: int) -> str:
    """格式化文件大小"""
    if size == 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size) < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

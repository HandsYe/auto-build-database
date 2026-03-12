"""
列表命令

列出可用的和已安装的数据库。
"""

from typing import Optional

import click

from biodeploy.adapters.adapter_registry import AdapterRegistry
from biodeploy.core.state_manager import StateManager


@click.command(name="list")
@click.option(
    "--installed",
    "-i",
    is_flag=True,
    help="仅显示已安装的数据库",
)
@click.option(
    "--available",
    "-a",
    is_flag=True,
    help="仅显示可用的数据库",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="输出格式",
)
@click.option(
    "--filter",
    help="按标签过滤",
)
@click.pass_context
def list_cmd(
    ctx: click.Context,
    installed: bool,
    available: bool,
    format: str,
    filter: Optional[str],
) -> None:
    """列出数据库

    显示可用的或已安装的数据库列表。

    示例:
        biodeploy list
        biodeploy list --installed
        biodeploy list --available
        biodeploy list --format json
    """
    state_manager = StateManager()
    registry = AdapterRegistry()

    # 如果没有指定，显示所有
    if not installed and not available:
        show_installed = True
        show_available = True
    else:
        show_installed = installed
        show_available = available

    output_data = []

    # 获取已安装的数据库
    if show_installed:
        installed_dbs = state_manager.get_installed_databases()
        for record in installed_dbs:
            output_data.append({
                "name": record.name,
                "version": record.version,
                "status": "installed",
                "path": str(record.install_path),
                "size": record.total_size,
                "install_time": record.install_time.isoformat(),
            })

    # 获取可用的数据库
    if show_available:
        available_adapters = registry.list_adapters()
        installed_names = {r.name for r in state_manager.get_installed_databases()}

        for adapter_name in available_adapters:
            if adapter_name not in installed_names:
                adapter = registry.get(adapter_name)
                if adapter:
                    metadata = adapter.get_metadata()
                    output_data.append({
                        "name": adapter_name,
                        "version": adapter.get_latest_version(),
                        "status": "available",
                        "display_name": metadata.display_name,
                        "description": metadata.description,
                    })

    # 输出结果
    if format == "json":
        import json
        click.echo(json.dumps(output_data, indent=2, ensure_ascii=False))
    elif format == "yaml":
        try:
            import yaml
            click.echo(yaml.dump(output_data, allow_unicode=True))
        except ImportError:
            click.echo("YAML support requires PyYAML")
    else:
        # 表格格式
        if not output_data:
            click.echo("没有数据库")
            return

        # 计算列宽
        name_width = max(len(str(d.get("name", ""))) for d in output_data) + 2
        version_width = max(len(str(d.get("version", ""))) for d in output_data) + 2
        status_width = 12

        # 打印表头
        header = (
            f"{'名称':<{name_width}} "
            f"{'版本':<{version_width}} "
            f"{'状态':<{status_width}} "
            f"{'描述/路径'}"
        )
        click.echo(header)
        click.echo("-" * len(header))

        # 打印数据
        for db in output_data:
            name = str(db.get("name", ""))
            version = str(db.get("version", ""))
            status = db.get("status", "")

            if status == "installed":
                desc = str(db.get("path", ""))
                status_color = "green"
            else:
                desc = str(db.get("description", ""))
                status_color = "blue"

            # 截断描述
            if len(desc) > 50:
                desc = desc[:47] + "..."

            line = (
                f"{name:<{name_width}} "
                f"{version:<{version_width}} "
            )
            click.echo(line, nl=False)
            click.secho(f"{status:<{status_width}} ", fg=status_color, nl=False)
            click.echo(desc)

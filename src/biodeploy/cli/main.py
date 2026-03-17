"""
命令行主入口

提供命令行工具的主入口点。
"""

from pathlib import Path
from typing import Optional

import click

from biodeploy import __version__
from biodeploy.infrastructure.config_manager import ConfigManager
from biodeploy.infrastructure.logger import setup_logging, get_logger

from biodeploy.cli.install_cmd import install
from biodeploy.cli.catalog_cmd import catalog_cmd
from biodeploy.cli.list_cmd import list_cmd
from biodeploy.cli.link_test_cmd import link_test_cmd
from biodeploy.cli.remove_cmd import remove
from biodeploy.cli.status_cmd import status
from biodeploy.cli.smoke_test_cmd import smoke_test_cmd
from biodeploy.cli.update_cmd import update


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=False),
    help="配置文件路径",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="增加日志详细程度 (可多次使用: -v, -vv, -vvv)",
)
@click.option("--quiet", "-q", is_flag=True, help="静默模式，只显示错误信息")
@click.version_option(version=__version__, prog_name="biodeploy")
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: int, quiet: bool) -> None:
    """BioDeploy - 生信数据库自动化部署系统

    这是一个用于生物信息学数据库自动化部署的工具，支持从数据下载到部署使用的全流程自动化。
    """
    # 确定日志级别
    if quiet:
        log_level = "ERROR"
    elif verbose >= 3:
        log_level = "DEBUG"
    elif verbose == 2:
        log_level = "INFO"
    elif verbose == 1:
        log_level = "WARNING"
    else:
        log_level = "INFO"

    # 设置日志
    setup_logging(level=log_level)

    # 初始化配置管理器
    config_manager = ConfigManager()
    if config:
        config_path = Path(config)
    else:
        config_path = None

    # 加载配置
    try:
        app_config = config_manager.load_global_config(config_path)
    except Exception as e:
        click.echo(f"加载配置失败: {e}", err=True)
        ctx.exit(1)

    # 保存到上下文
    ctx.ensure_object(dict)
    ctx.obj["config_manager"] = config_manager
    ctx.obj["config"] = app_config
    ctx.obj["logger"] = get_logger("cli")


cli.add_command(install)
cli.add_command(catalog_cmd)
cli.add_command(smoke_test_cmd)
cli.add_command(link_test_cmd)
cli.add_command(update)
cli.add_command(list_cmd)
cli.add_command(remove)
cli.add_command(status)


if __name__ == "__main__":
    cli()

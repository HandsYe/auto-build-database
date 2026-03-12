"""
命令行主入口

提供命令行工具的主入口点。
"""

import click
from pathlib import Path
from typing import Optional

from biodeploy import __version__
from biodeploy.infrastructure.config_manager import ConfigManager
from biodeploy.infrastructure.logger import setup_logging, get_logger


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


@cli.command()
@click.argument("databases", nargs=-1, required=True)
@click.option("--path", type=click.Path(), help="安装路径")
@click.option("--version", help="指定版本")
@click.option("--parallel", type=int, default=1, help="并发数 (默认: 1)")
@click.option("--force", is_flag=True, help="强制重新安装")
@click.option("--skip-deps", is_flag=True, help="跳过依赖检查")
@click.option("--no-index", is_flag=True, help="不构建索引")
@click.option("--no-env", is_flag=True, help="不设置环境变量")
@click.pass_context
def install(
    ctx: click.Context,
    databases: tuple[str, ...],
    path: Optional[str],
    version: Optional[str],
    parallel: int,
    force: bool,
    skip_deps: bool,
    no_index: bool,
    no_env: bool,
) -> None:
    """安装数据库

    安装一个或多个生信数据库。

    示例:
        biodeploy install ncbi
        biodeploy install ncbi ensembl ucsc
        biodeploy install ncbi --version 2024.01 --path /data/bio/ncbi
    """
    logger = ctx.obj["logger"]
    config = ctx.obj["config"]

    logger.info(f"开始安装数据库: {', '.join(databases)}")

    # 准备安装选项
    options = {
        "path": path or str(config.install.default_install_path),
        "version": version,
        "parallel": parallel,
        "force": force,
        "skip_deps": skip_deps,
        "no_index": no_index,
        "no_env": no_env,
    }

    # TODO: 调用安装管理器
    click.echo(f"准备安装以下数据库: {', '.join(databases)}")
    click.echo(f"安装路径: {options['path']}")
    click.echo(f"并发数: {parallel}")

    if force:
        click.echo("强制重新安装: 是")

    click.echo("\n安装功能正在开发中...")


@cli.command()
@click.argument("databases", nargs=-1, required=False)
@click.option("--check-only", is_flag=True, help="仅检查更新，不实际更新")
@click.option("--keep-old", is_flag=True, help="保留旧版本")
@click.option("--parallel", type=int, default=1, help="并发数 (默认: 1)")
@click.pass_context
def update(
    ctx: click.Context,
    databases: Optional[tuple[str, ...]],
    check_only: bool,
    keep_old: bool,
    parallel: int,
) -> None:
    """更新数据库

    检查并更新已安装的数据库。

    示例:
        biodeploy update --check-only
        biodeploy update ncbi ensembl
        biodeploy update --keep-old
    """
    logger = ctx.obj["logger"]

    if databases:
        logger.info(f"检查更新: {', '.join(databases)}")
    else:
        logger.info("检查所有数据库的更新")

    # TODO: 调用更新管理器
    if check_only:
        click.echo("仅检查更新模式")
    else:
        click.echo("更新功能正在开发中...")


@cli.command()
@click.option("--installed", is_flag=True, help="仅显示已安装的数据库")
@click.option("--available", is_flag=True, help="仅显示可用的数据库")
@click.option("--all", "show_all", is_flag=True, help="显示所有数据库 (默认)")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "yaml"]), default="table", help="输出格式")
@click.option("--filter", "filter_tag", help="按标签过滤")
@click.pass_context
def list(
    ctx: click.Context,
    installed: bool,
    available: bool,
    show_all: bool,
    output_format: str,
    filter_tag: Optional[str],
) -> None:
    """列出数据库

    列出可用或已安装的数据库。

    示例:
        biodeploy list
        biodeploy list --installed
        biodeploy list --format json
    """
    logger = ctx.obj["logger"]

    # TODO: 调用状态管理器获取数据库列表
    click.echo("数据库列表功能正在开发中...")

    # 示例输出
    if installed:
        click.echo("\n已安装的数据库:")
        click.echo("  (暂无)")
    else:
        click.echo("\n可用的数据库:")
        click.echo("  - ncbi (NCBI数据库)")
        click.echo("  - ensembl (Ensembl数据库)")
        click.echo("  - ucsc (UCSC数据库)")


@cli.command()
@click.argument("databases", nargs=-1, required=True)
@click.option("--version", help="指定版本 (不指定则卸载所有版本)")
@click.option("--force", is_flag=True, help="强制卸载，不提示确认")
@click.option("--keep-config", is_flag=True, help="保留配置文件")
@click.pass_context
def remove(
    ctx: click.Context,
    databases: tuple[str, ...],
    version: Optional[str],
    force: bool,
    keep_config: bool,
) -> None:
    """卸载数据库

    卸载一个或多个已安装的数据库。

    示例:
        biodeploy remove ncbi
        biodeploy remove ncbi --version 2024.01
        biodeploy remove ncbi ensembl --force
    """
    logger = ctx.obj["logger"]

    logger.info(f"准备卸载数据库: {', '.join(databases)}")

    # 确认卸载
    if not force:
        if not click.confirm(f"确定要卸载以下数据库吗? {', '.join(databases)}"):
            click.echo("取消卸载")
            return

    # TODO: 调用卸载管理器
    click.echo(f"卸载功能正在开发中...")


@cli.command()
@click.argument("database", required=False)
@click.option("--detail", is_flag=True, help="显示详细信息")
@click.option("--json", "json_output", is_flag=True, help="以JSON格式输出")
@click.pass_context
def status(
    ctx: click.Context,
    database: Optional[str],
    detail: bool,
    json_output: bool,
) -> None:
    """查看状态

    查看数据库安装状态。

    示例:
        biodeploy status
        biodeploy status ncbi
        biodeploy status ncbi --detail
    """
    logger = ctx.obj["logger"]

    if database:
        logger.info(f"查看数据库状态: {database}")
    else:
        logger.info("查看所有数据库状态")

    # TODO: 调用状态管理器
    click.echo("状态查询功能正在开发中...")


if __name__ == "__main__":
    cli()

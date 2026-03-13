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

    # 调用安装管理器
    try:
        from biodeploy.core.installation_manager import InstallationManager
        
        manager = InstallationManager(install_path=Path(options["path"]))
        
        click.echo(f"准备安装以下数据库: {', '.join(databases)}")
        click.echo(f"安装路径: {options['path']}")
        click.echo(f"并发数: {parallel}")
        
        if force:
            click.echo("强制重新安装: 是")
        
        # 定义进度回调
        def progress_callback(message: str, progress: float):
            if progress < 1.0:
                click.echo(f"[{progress*100:.0f}%] {message}")
        
        # 执行安装
        success_count = 0
        for db in databases:
            click.echo(f"\n正在安装: {db}")
            try:
                success = manager.install(
                    database=db,
                    version=version,
                    install_path=Path(options["path"]) / db if path else None,
                    options=options,
                    progress_callback=progress_callback,
                )
                if success:
                    click.echo(f"✓ {db} 安装成功")
                    success_count += 1
                else:
                    click.echo(f"✗ {db} 安装失败", err=True)
            except Exception as e:
                click.echo(f"✗ {db} 安装失败: {e}", err=True)
        
        click.echo(f"\n安装完成: {success_count}/{len(databases)} 成功")
        
    except Exception as e:
        logger.error(f"安装失败: {e}")
        click.echo(f"安装失败: {e}", err=True)
        ctx.exit(1)


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

    # 调用更新管理器
    try:
        from biodeploy.core.update_manager import UpdateManager
        from biodeploy.core.state_manager import StateManager
        
        manager = UpdateManager()
        state_manager = StateManager()
        
        if check_only:
            click.echo("检查更新模式")
            
            # 获取已安装的数据库
            installed = state_manager.get_installed_databases()
            
            if not installed:
                click.echo("没有已安装的数据库")
                return
            
            click.echo(f"\n已安装的数据库:")
            for record in installed:
                click.echo(f"  - {record.name} ({record.version})")
                
                # 检查更新
                try:
                    latest = manager.check_latest_version(record.name)
                    if latest and latest != record.version:
                        click.echo(f"    有新版本可用: {latest}")
                    else:
                        click.echo(f"    已是最新版本")
                except Exception as e:
                    click.echo(f"    检查失败: {e}")
        else:
            click.echo("更新功能正在执行...")
            
            # 获取要更新的数据库列表
            if databases:
                db_list = list(databases)
            else:
                installed = state_manager.get_installed_databases()
                db_list = [r.name for r in installed]
            
            success_count = 0
            for db in db_list:
                click.echo(f"\n正在更新: {db}")
                try:
                    success = manager.update(
                        database=db,
                        options={"keep_old": keep_old}
                    )
                    if success:
                        click.echo(f"✓ {db} 更新成功")
                        success_count += 1
                    else:
                        click.echo(f"✗ {db} 更新失败", err=True)
                except Exception as e:
                    click.echo(f"✗ {db} 更新失败: {e}", err=True)
            
            click.echo(f"\n更新完成: {success_count}/{len(db_list)} 成功")
            
    except Exception as e:
        logger.error(f"更新失败: {e}")
        click.echo(f"更新失败: {e}", err=True)
        ctx.exit(1)


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

    # 调用状态管理器获取数据库列表
    try:
        from biodeploy.core.state_manager import StateManager
        from biodeploy.adapters.adapter_registry import AdapterRegistry
        
        state_manager = StateManager()
        registry = AdapterRegistry()
        
        if installed:
            # 显示已安装的数据库
            installed_dbs = state_manager.get_installed_databases()
            
            if not installed_dbs:
                click.echo("没有已安装的数据库")
                return
            
            click.echo("\n已安装的数据库:")
            for record in installed_dbs:
                status_icon = "✓" if record.status.value == "completed" else "✗"
                click.echo(f"  {status_icon} {record.name} ({record.version})")
                click.echo(f"      路径: {record.install_path}")
                click.echo(f"      状态: {record.status.value}")
        else:
            # 显示可用的数据库
            available = registry.list_adapters()
            
            if not available:
                click.echo("没有可用的数据库适配器")
                return
            
            click.echo("\n可用的数据库:")
            for db_name in available:
                try:
                    adapter = registry.get(db_name)
                    if adapter:
                        metadata = adapter.get_metadata()
                        click.echo(f"  - {db_name}")
                        click.echo(f"      名称: {metadata.display_name}")
                        click.echo(f"      描述: {metadata.description}")
                        click.echo(f"      大小: {metadata.size / (1024**3):.2f} GB")
                except Exception as e:
                    click.echo(f"  - {db_name} (信息获取失败)")
                    
    except Exception as e:
        logger.error(f"获取数据库列表失败: {e}")
        click.echo(f"获取数据库列表失败: {e}", err=True)
        ctx.exit(1)


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

    # 调用卸载管理器
    try:
        from biodeploy.core.uninstall_manager import UninstallManager
        
        manager = UninstallManager()
        
        success_count = 0
        for db in databases:
            click.echo(f"\n正在卸载: {db}")
            try:
                success = manager.uninstall(
                    database=db,
                    options={"keep_config": keep_config, "force": force}
                )
                if success:
                    click.echo(f"✓ {db} 卸载成功")
                    success_count += 1
                else:
                    click.echo(f"✗ {db} 卸载失败", err=True)
            except Exception as e:
                click.echo(f"✗ {db} 卸载失败: {e}", err=True)
        
        click.echo(f"\n卸载完成: {success_count}/{len(databases)} 成功")
        
    except Exception as e:
        logger.error(f"卸载失败: {e}")
        click.echo(f"卸载失败: {e}", err=True)
        ctx.exit(1)


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

    # 调用状态管理器
    try:
        from biodeploy.core.state_manager import StateManager
        import json as json_module
        
        state_manager = StateManager()
        
        if database:
            # 查看指定数据库的状态
            record = state_manager.get_database_info(database)
            
            if not record:
                click.echo(f"数据库 {database} 未安装")
                return
            
            if json_output:
                # JSON格式输出
                data = {
                    "name": record.name,
                    "version": record.version,
                    "status": record.status.value,
                    "install_path": str(record.install_path),
                    "install_time": record.install_time.isoformat(),
                }
                click.echo(json_module.dumps(data, indent=2, ensure_ascii=False))
            else:
                # 文本格式输出
                click.echo(f"\n数据库: {record.name}")
                click.echo(f"版本: {record.version}")
                click.echo(f"状态: {record.status.value}")
                click.echo(f"安装路径: {record.install_path}")
                click.echo(f"安装时间: {record.install_time}")
                
                if detail:
                    click.echo(f"\n详细信息:")
                    click.echo(f"  文件数量: {record.file_count}")
                    click.echo(f"  总大小: {record.total_size / (1024**3):.2f} GB")
                    if record.indexes:
                        click.echo(f"  已构建索引: {', '.join(record.indexes)}")
        else:
            # 查看所有数据库的状态
            all_dbs = state_manager.get_installed_databases()
            
            if not all_dbs:
                click.echo("没有已安装的数据库")
                return
            
            if json_output:
                # JSON格式输出
                data = [
                    {
                        "name": r.name,
                        "version": r.version,
                        "status": r.status.value,
                        "install_path": str(r.install_path),
                    }
                    for r in all_dbs
                ]
                click.echo(json_module.dumps(data, indent=2, ensure_ascii=False))
            else:
                # 文本格式输出
                click.echo("\n已安装的数据库:")
                for record in all_dbs:
                    status_icon = "✓" if record.status.value == "completed" else "✗"
                    click.echo(f"  {status_icon} {record.name} ({record.version})")
                    click.echo(f"      状态: {record.status.value}")
                    click.echo(f"      路径: {record.install_path}")
                    
                    if detail:
                        click.echo(f"      安装时间: {record.install_time}")
                        click.echo(f"      大小: {record.total_size / (1024**3):.2f} GB")
                    
    except Exception as e:
        logger.error(f"查询状态失败: {e}")
        click.echo(f"查询状态失败: {e}", err=True)
        ctx.exit(1)


if __name__ == "__main__":
    cli()

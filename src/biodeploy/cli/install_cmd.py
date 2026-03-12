"""
安装命令

处理数据库安装相关的命令行操作。
"""

from pathlib import Path
from typing import List, Optional

import click

from biodeploy.core.installation_manager import InstallationManager
from biodeploy.infrastructure.config_manager import ConfigManager
from biodeploy.infrastructure.logger import logger


@click.command(name="install")
@click.argument("databases", nargs=-1, required=True)
@click.option(
    "--path",
    "-p",
    type=click.Path(),
    help="安装路径",
)
@click.option(
    "--version",
    "-v",
    help="指定版本",
)
@click.option(
    "--parallel",
    "-j",
    type=int,
    default=1,
    help="并发安装数量",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="强制重新安装",
)
@click.option(
    "--skip-deps",
    is_flag=True,
    help="跳过依赖检查",
)
@click.option(
    "--no-index",
    is_flag=True,
    help="不构建索引",
)
@click.option(
    "--set-env",
    is_flag=True,
    help="设置环境变量",
)
@click.option(
    "--mirror",
    help="使用指定镜像",
)
@click.pass_context
def install(
    ctx: click.Context,
    databases: tuple,
    path: Optional[str],
    version: Optional[str],
    parallel: int,
    force: bool,
    skip_deps: bool,
    no_index: bool,
    set_env: bool,
    mirror: Optional[str],
) -> None:
    """安装一个或多个数据库

    DATABASES 是要安装的数据库名称列表。

    示例:
        biodeploy install ncbi
        biodeploy install ncbi ensembl ucsc
        biodeploy install ncbi --version 2024.01 --path /data/bio
        biodeploy install ncbi ensembl --parallel 2
    """
    config = ctx.obj["config"]
    log = logger.get_logger("cli.install")

    # 构建安装选项
    options = {
        "force": force,
        "skip_deps": skip_deps,
        "no_index": no_index,
        "set_env": set_env,
        "parallel": parallel > 1,
        "max_parallel": parallel,
    }

    if mirror:
        options["mirror"] = mirror

    # 确定安装路径
    install_path = Path(path) if path else config.install.default_install_path

    # 创建安装管理器
    manager = InstallationManager(install_path=install_path)

    # 安装数据库
    if len(databases) == 1:
        # 单个数据库安装，显示进度
        db_name = databases[0]

        with click.progressbar(
            length=100,
            label=f"安装 {db_name}",
        ) as bar:
            def progress_callback(message: str, progress: float):
                bar.label = f"安装 {db_name}: {message}"
                bar.update(int(progress * 100) - bar.pos)

            success = manager.install(
                db_name,
                version=version,
                install_path=install_path / db_name / (version or "latest"),
                options=options,
                progress_callback=progress_callback,
            )

        if success:
            click.secho(f"✓ {db_name} 安装成功", fg="green")
        else:
            click.secho(f"✗ {db_name} 安装失败", fg="red")
            ctx.exit(1)
    else:
        # 批量安装
        click.echo(f"开始安装 {len(databases)} 个数据库...")

        results = manager.install_multiple(list(databases), options)

        # 显示结果
        success_count = sum(1 for r in results.values() if r)
        failed_count = len(results) - success_count

        click.echo()
        click.echo("安装结果:")
        for db_name, success in results.items():
            if success:
                click.secho(f"  ✓ {db_name}", fg="green")
            else:
                click.secho(f"  ✗ {db_name}", fg="red")

        click.echo()
        click.echo(f"成功: {success_count}, 失败: {failed_count}")

        if failed_count > 0:
            ctx.exit(1)

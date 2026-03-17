"""
Catalog 命令

输出“当前代码实际支持下载”的数据库清单（权威来源：AdapterRegistry）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click

from biodeploy.adapters.adapter_registry import AdapterRegistry


@click.command(name="catalog")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml", "md"]),
    default="table",
    help="输出格式",
)
@click.option("--filter", "filter_tag", help="按标签过滤（精确匹配 tags）")
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    help="输出到文件（默认输出到stdout）",
)
@click.pass_context
def catalog_cmd(
    ctx: click.Context,
    output_format: str,
    filter_tag: Optional[str],
    output: Optional[str],
) -> None:
    """输出可下载数据库清单

示例:
  biodeploy catalog
  biodeploy catalog -f json -o biodeploy-catalog.json
  biodeploy catalog --filter ncbi -f md -o catalog.md
    """
    registry = AdapterRegistry()

    rows: list[dict] = []
    for name in registry.list_adapters():
        adapter = registry.get(name)
        if not adapter:
            continue
        try:
            md = adapter.get_metadata()
        except Exception:
            # 避免某个适配器元数据异常影响整体清单输出
            continue

        tags = getattr(md, "tags", []) or []
        if filter_tag and filter_tag not in set(tags):
            continue

        rows.append(
            {
                "name": name,
                "display_name": md.display_name,
                "description": md.description,
                "version": adapter.get_latest_version(),
                "size": md.size,
                "tags": tags,
                "sources": [s.url for s in md.download_sources],
            }
        )

    rows.sort(key=lambda r: r["name"])

    def emit(text: str) -> None:
        if output:
            Path(output).write_text(text + "\n", encoding="utf-8")
        else:
            click.echo(text)

    if output_format == "json":
        import json

        emit(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    if output_format == "yaml":
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise RuntimeError("YAML 输出需要安装 PyYAML") from e
        emit(yaml.dump(rows, allow_unicode=True, sort_keys=False))
        return

    if output_format == "md":
        lines: list[str] = []
        lines.append("| name | version | size(GB) | tags | description |")
        lines.append("| --- | --- | ---: | --- | --- |")
        for r in rows:
            size_gb = (r.get("size") or 0) / (1024**3)
            tags = ", ".join(r.get("tags") or [])
            desc = (r.get("description") or "").replace("\n", " ").strip()
            if len(desc) > 80:
                desc = desc[:77] + "..."
            lines.append(
                f"| `{r['name']}` | {r.get('version','')} | {size_gb:.2f} | {tags} | {desc} |"
            )
        emit("\n".join(lines))
        return

    # table
    if not rows:
        emit("没有可下载数据库")
        return

    name_w = max(len(r["name"]) for r in rows) + 2
    ver_w = max(len(str(r.get("version", ""))) for r in rows) + 2
    size_w = 10

    header = f"{'名称':<{name_w}} {'版本':<{ver_w}} {'大小(GB)':>{size_w}} 描述"
    lines = [header, "-" * len(header)]
    for r in rows:
        size_gb = (r.get("size") or 0) / (1024**3)
        desc = (r.get("description") or "").replace("\n", " ").strip()
        if len(desc) > 80:
            desc = desc[:77] + "..."
        lines.append(f"{r['name']:<{name_w}} {str(r.get('version','')):<{ver_w}} {size_gb:>{size_w}.2f} {desc}")
    emit("\n".join(lines))


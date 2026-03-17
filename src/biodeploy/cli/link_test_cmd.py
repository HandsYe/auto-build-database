"""
Link-test 命令

对每个数据库的下载源做“链路可达性”探测（轻量，不做全量下载）。
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import click
import requests

from biodeploy.adapters.adapter_registry import AdapterRegistry


def _probe_url(url: str, timeout_s: float) -> dict:
    start = time.time()
    # 先 HEAD；如果不支持/失败再用 Range GET 取 1 byte
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout_s)
        ok = 200 <= r.status_code < 400
        return {
            "url": url,
            "ok": ok,
            "method": "HEAD",
            "status_code": r.status_code,
            "elapsed_ms": int((time.time() - start) * 1000),
            "content_length": r.headers.get("content-length"),
        }
    except Exception as e:
        head_err = str(e)

    try:
        headers = {"Range": "bytes=0-0"}
        with requests.get(url, headers=headers, stream=True, allow_redirects=True, timeout=timeout_s) as r:
            # 读取一点点触发连接
            _ = next(r.iter_content(chunk_size=1), b"")
            ok = 200 <= r.status_code < 400
            return {
                "url": url,
                "ok": ok,
                "method": "GET_RANGE",
                "status_code": r.status_code,
                "elapsed_ms": int((time.time() - start) * 1000),
                "content_length": r.headers.get("content-length"),
                "head_error": head_err,
            }
    except Exception as e:
        return {
            "url": url,
            "ok": False,
            "method": "GET_RANGE",
            "status_code": None,
            "elapsed_ms": int((time.time() - start) * 1000),
            "error": str(e),
            "head_error": head_err,
        }


@click.command(name="link-test")
@click.option("--all", "test_all", is_flag=True, help="测试所有数据库（默认）")
@click.option("--database", "-d", help="只测试指定数据库名称")
@click.option(
    "--timeout",
    type=float,
    default=5.0,
    show_default=True,
    help="单个 URL 探测超时（秒）",
)
@click.option(
    "--max-sources",
    type=int,
    default=3,
    show_default=True,
    help="每个数据库最多探测多少个下载源 URL",
)
@click.option(
    "--limit",
    type=int,
    default=0,
    show_default=True,
    help="只测试前 N 个数据库（调试用，0 表示不限制）",
)
@click.option(
    "--no-network",
    is_flag=True,
    help="不发起网络请求，仅输出将要测试的数据库/URL（用于离线/单测）",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="输出格式",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, writable=True),
    help="输出到文件（默认输出到stdout）",
)
@click.pass_context
def link_test_cmd(
    ctx: click.Context,
    test_all: bool,
    database: Optional[str],
    timeout: float,
    max_sources: int,
    limit: int,
    no_network: bool,
    output_format: str,
    output: Optional[str],
) -> None:
    """对所有数据库做下载链路探测（轻量）"""
    registry = AdapterRegistry()

    names = [database] if database else registry.list_adapters()
    if limit and limit > 0:
        names = names[:limit]

    report: list[dict] = []
    for name in names:
        adapter = registry.get(name)
        if not adapter:
            report.append({"name": name, "ok": False, "error": "adapter_not_found", "probes": []})
            continue

        try:
            md = adapter.get_metadata()
        except Exception as e:
            report.append({"name": name, "ok": False, "error": f"metadata_error: {e}", "probes": []})
            continue

        urls = [s.url for s in md.download_sources][:max_sources]
        probes = []
        if no_network:
            probes = [{"url": u, "ok": None, "method": None, "status_code": None} for u in urls]
            ok = True
        else:
            probes = [_probe_url(u, timeout_s=timeout) for u in urls]
            ok = any(p.get("ok") for p in probes) if probes else False

        report.append(
            {
                "name": name,
                "display_name": md.display_name,
                "ok": ok,
                "probes": probes,
            }
        )

    def emit(text: str) -> None:
        if output:
            Path(output).write_text(text + "\n", encoding="utf-8")
        else:
            click.echo(text)

    if output_format == "json":
        import json

        emit(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if output_format == "yaml":
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise RuntimeError("YAML 输出需要安装 PyYAML") from e
        emit(yaml.dump(report, allow_unicode=True, sort_keys=False))
        return

    # table
    total = len(report)
    ok_count = sum(1 for r in report if r.get("ok"))
    bad_count = total - ok_count
    lines = [f"link-test: ok {ok_count}/{total}, failed {bad_count}"]
    lines.append("")
    for r in report:
        status = "OK" if r.get("ok") else "FAIL"
        lines.append(f"- {status:4} {r.get('name')}")
        for p in r.get("probes", [])[:max_sources]:
            sc = p.get("status_code")
            method = p.get("method")
            u = p.get("url")
            pok = p.get("ok")
            lines.append(f"    - {method} {sc} ok={pok} {u}")
    emit("\n".join(lines))


from __future__ import annotations

import json

from click.testing import CliRunner

from biodeploy.cli.main import cli


def test_catalog_json_is_parseable():
    runner = CliRunner()
    result = runner.invoke(cli, ["catalog", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert any(d.get("name") == "kegg_pathway" for d in data)


def test_catalog_md_has_header():
    runner = CliRunner()
    result = runner.invoke(cli, ["catalog", "--format", "md"])
    assert result.exit_code == 0
    assert "| name | version | size(GB) | tags | description |" in result.output


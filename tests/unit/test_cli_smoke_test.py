from __future__ import annotations

from click.testing import CliRunner

from biodeploy.cli.main import cli


def test_smoke_test_local_only():
    runner = CliRunner()
    result = runner.invoke(cli, ["smoke-test"])
    assert result.exit_code == 0
    assert "本地自检通过" in result.output


from __future__ import annotations

import json

from click.testing import CliRunner

from biodeploy.cli.main import cli


def test_link_test_no_network_json_parseable():
    runner = CliRunner()
    result = runner.invoke(cli, ["link-test", "--no-network", "--limit", "2", "-f", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2


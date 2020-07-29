from click.testing import CliRunner
from gitmine.gitmine import go, get, config
from gitmine.commands.config import get_or_create_github_config

runner = CliRunner()

def test_config_username_returns_specified():
    result = runner.invoke(config, ["username"])
    assert result.output == ""

def test_config_bad_prop_errors():
    result = runner.invoke(config, ["banana-boat"])
    assert result.exit_code == 2  # should fail
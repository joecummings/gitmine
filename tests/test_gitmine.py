from click.testing import CliRunner

from gitmine.commands.config import get_or_create_github_config
from gitmine.gitmine import config, get, gitmine, go

runner = CliRunner()

def test_gitmine_without_command():
    result = runner.invoke(gitmine, [])
    assert result.exit_code == 0


def test_gitmine_verbose():
    with runner.isolated_filesystem():
        result = runner.invoke(gitmine, ["config", "username", "abc", "-v"])
        assert result.exit_code == 0
        assert "Logging level set to INFO." in result.output


def test_gitmine_vverbose():
    with runner.isolated_filesystem():
        result = runner.invoke(gitmine, ["config", "username", "abc", "-vv"])
        assert result.exit_code == 0
        assert "Logging level set to DEBUG." in result.output


def test_get_version():
    from gitmine.version import __version__

    result = runner.invoke(gitmine, ["--version"])
    assert result.output == f"gitmine, version {__version__}\n"

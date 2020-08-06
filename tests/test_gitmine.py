import logging

from click.testing import CliRunner

from gitmine.commands.config import get_or_create_github_config
from gitmine.constants import LOGGER
from gitmine.gitmine import config, get, gitmine, go

logger = logging.getLogger(LOGGER)

runner = CliRunner()

# GITMINE - General


def test_gitmine_without_command():
    result = runner.invoke(gitmine, [])
    assert result.exit_code == 0


def test_gitmine_verbose():
    result = runner.invoke(gitmine, ["-v", "config", "username", "abc"])
    assert result.exit_code == 0
    assert logger.level == 40


def test_gitmine_vverbose():
    result = runner.invoke(gitmine, ["-vv", "config", "username", "abc"])
    assert result.exit_code == 0
    assert logger.level == 20


def test_gitmine_vvverbose():
    result = runner.invoke(gitmine, ["-vvv", "config", "username", "abc"])
    assert result.exit_code == 0
    assert logger.level == 10

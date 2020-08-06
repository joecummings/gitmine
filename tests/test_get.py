import json
from typing import Dict

import click
import pytest
from click.testing import CliRunner

from gitmine.commands.get import print_issues, print_prs
from gitmine.gitmine import gitmine  # gitmine?
from test_constants import TEST_ISSUES_PATH, TEST_PRS_PATH

runner = CliRunner()

test_issues: Dict[str, str] = {}
test_prs: Dict[str, str] = {}


@pytest.fixture
def get_configuration():

    with open(TEST_ISSUES_PATH, "r") as issues_handle:
        test_issue = json.load(issues_handle)  #'response': ... 'output': ....
    with open(TEST_PRS_PATH, "r") as prs_handle:
        test_prs = json.load(prs_handle)


def base_runner(options):
    command = ["get"]
    command.extend(options)
    return runner.invoke(gitmine, command)


def test_get_none():
    result = base_runner([""])
    assert result.exit_code == 2


def test_get_bad_argument():
    with pytest.raises(click.BadArgumentUsage):
        result = base_runner(["banana-boat"])
    assert result.exit_code == 2


def test_get_bad_argument2():
    with pytest.raises(click.BadArgumentUsage):
        result = base_runner(["banana-boat"])
    assert result.exit_code == 2


def test_get_issues_option_asc_color():
    pass


def test_get_issues_option_asc_nocolor():
    pass


def test_get_issues_opetion_desc_color():
    pass


def test_get_issues_option_desc_nocolorr():
    pass


def test_get_all():
    pass


def test_get_bad_credentials():
    pass

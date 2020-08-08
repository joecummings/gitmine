import json
from typing import Dict

import click
import pytest
from click.testing import CliRunner
from test_constants import TEST_ISSUES_PATH, TEST_PRS_PATH

from gitmine.commands.get import print_issues, print_prs
from gitmine.gitmine import gitmine  # gitmine?

runner = CliRunner()


@pytest.fixture(scope="module")
def get_configuration():
    data = {}

    with open(TEST_ISSUES_PATH, "r") as issues_handle:
        issue_data = json.load(issues_handle)
        data["issue"] = issue_data["issues"]
        data["issue_output"] = issue_data["print_output"]

    with open(TEST_PRS_PATH, "r") as prs_handle:
        issue_data = json.load(prs_handle)

    yield data


def base_runner(options):
    command = ["get"]
    command.extend(options)
    return runner.invoke(gitmine, command)


def test_get_none():
    result = base_runner([""])
    assert result.exit_code == 2


def test_get_bad_argument():
    result = base_runner(["banana-boat"])
    assert result.exit_code == 2


def test_get_bad_argument2():
    result = base_runner(["banana-boat"])
    assert result.exit_code == 2


def test_get_issues(capsys):
    pass
    # with open(TEST_ISSUES_PATH, "r") as issues_handle:
    #     json_dict = json.load(issues_handle)
    #     issues = json_dict["issues"]
    #     print_output = json_dict["print_output"]["11"]
    #     print_issues(issues, color=False, asc=True)
    #     captured = capsys.readouterr()
    #     captured_out = captured.out.replace("\n", "").split("#") # Don't care about newlines
    # for issue in captured_out:
    #     assert issue in print_output


def test_get_issues_spec_repo():
    # specify repository to pull from and make sure only those get returned
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

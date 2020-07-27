import click
from datetime import datetime, timedelta
from typing import Any, List, Mapping
from gitmine.utils import catch_bad_responses
import requests
from collections import defaultdict

import pprint

class GithubElement:
    """ Container for Github Issue or Pull Request
    """

    def __init__(
        self, type: str, title: str, number: int, url: str, elapsed_time: timedelta
    ) -> None:
        self.type = type
        self.title = title
        self.number = number
        self.url = url
        self.elapsed_time = elapsed_time

    def __repr__(self) -> str:
        return f"{click.style(''.join(['#', str(self.number)]), fg=self._elapsed_time_to_color())} {self.title}"

    def _elapsed_time_to_color(self) -> str:
        if self.elapsed_time < timedelta(days=1):
            return "green"
        if self.elapsed_time < timedelta(days=3):
            return "yellow"
        return "red"

def get_prs(ctx: click.Context, headers: Mapping[str, str]) -> List[Mapping[str, Any]]:
    """ Get all Github PRs assigned to user.
    """

    username = ctx.obj.get_value("username")
    url_format = f"https://api.github.com/search/issues?q=is:open+is:pr+review-requested:{username}"
    response = requests.get(url_format, headers=headers)
    catch_bad_responses(response)
    return response.json()["items"]


def get_issues(headers: Mapping[str, str]) -> List[Mapping[str, Any]]:
    """ Get all Github Issues assigned to user.
    """

    url_format = "https://api.github.com/issues"
    response = requests.get(url_format, headers=headers)
    catch_bad_responses(response)
    return response.json()


def print_issues(issues: List[Mapping[str, Any]]) -> None:
    """ Print issues in the following format:

    repo-title
    #issue-number issue-title
    ...
    """

    projects = defaultdict(list)

    for issue in issues:
        curr_project = issue["repository"]["full_name"]
        projects[curr_project].append(
            GithubElement(
                type="Issue",
                title=issue["title"],
                number=issue["number"],
                url=issue["html_url"],
                elapsed_time=datetime.now()
                - datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
            )
        )

    for project, issues in projects.items():
        click.echo(project)
        for issue in issues:
            click.echo(issue)
        click.echo()


def get_command(ctx: click.Context, spec: str) -> None:
    """ Implementation of the *get* command.
    """

    headers = {"Authorization": f"Bearer {ctx.obj.get_value('token')}"}
    if spec == "issues":
        res = get_issues(headers=headers)
        print_issues(res)
    elif spec == "prs":
        pass
        # res = get_prs(ctx, headers=headers)
        # print_issues(res)
    elif spec == "all":
        res = get_issues(headers=headers)
        print_issues(res)
        click.echo(f"*" * 20)
        # res = _get_prs(headers=headers)
        # _print_prs(res)
    else:
        raise click.BadArgumentUsage(message=f"Unkown spec: {spec}")

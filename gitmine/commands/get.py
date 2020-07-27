import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, List, Mapping

import click
import requests

from gitmine.utils import catch_bad_responses


class GithubElement:
    """ Container for Github Issue or Pull Request.
    """

    def __init__(
        self, type: str, title: str, number: int, url: str, elapsed_time: timedelta, color_coded: bool
    ) -> None:
        self.type = type
        self.title = title
        self.number = number
        self.url = url
        self.elapsed_time = elapsed_time
        self.color_coded = color_coded

    def __repr__(self) -> str:
        return f"{click.style(''.join(['#', str(self.number)]), fg=self._elapsed_time_to_color())} {self.title}"

    def _elapsed_time_to_color(self) -> str:
        if not self.color_coded:
            return "white"

        if self.elapsed_time < timedelta(days=1):
            return "green"
        if self.elapsed_time < timedelta(days=3):
            return "yellow"
        return "red"


class Issue(GithubElement):
    """ Github Issue
    """

    def __init__(self, title: str, number: str, url: str, elapsed_time: timedelta, color_coded: bool):
        super().__init__(
            type="Issue",
            title=title,
            number=number,
            url=url,
            elapsed_time=elapsed_time,
            color_coded=color_coded
        )

class PullRequest(GithubElement):
    """ Github Pull Request
    """

    def __init__(self, title: str, number: str, url: str, elapsed_time: timedelta, color_coded: bool):
        super().__init__(
            type="PullRequest",
            title=title,
            number=number,
            url=url,
            elapsed_time=elapsed_time,
            color_coded=color_coded
        )

def get_prs(ctx: click.Context, headers: Mapping[str, str]) -> List[Mapping[str, Any]]:
    """ Get all Github PRs assigned to user.
    """

    username = ctx.obj.get_value("username")
    url_format = f"https://api.github.com/search/issues?q=is:open+is:pr+review-requested:{username}"
    response = requests.get(url_format, headers=headers)
    catch_bad_responses(response)
    return response.json()["items"]


def print_prs(prs: List[Mapping[str, Any]], color: bool) -> None:
    """ Print PRs in the following format:

    repo-title
    #pr-number pr-title
    ...
    """

    projects = defaultdict(list)

    for pr in prs:
        url = pr["html_url"]
        curr_project = re.findall(r"github.com/(.+?)/pull", url)[0]
        projects[curr_project].append(
            PullRequest(
                title=pr["title"],
                number=pr["number"],
                url=url,
                elapsed_time=datetime.now()
                - datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                color_coded=True if color else False
            )
        )

    for project, elements in projects.items():
        click.echo(project)
        for element in elements:
            click.echo(element)
        click.echo()


def get_issues(headers: Mapping[str, str]) -> List[Mapping[str, Any]]:
    """ Get all Github Issues assigned to user.
    """

    url_format = "https://api.github.com/issues"
    response = requests.get(url_format, headers=headers)
    catch_bad_responses(response)
    return response.json()


def print_issues(issues: List[Mapping[str, Any]], color: bool) -> None:
    """ Print issues in the following format:

    repo-title
    #issue-number issue-title
    ...
    """

    projects = defaultdict(list)

    for issue in issues:
        curr_project = issue["repository"]["full_name"]
        projects[curr_project].append(
            Issue(
                title=issue["title"],
                number=issue["number"],
                url=issue["html_url"],
                elapsed_time=datetime.now()
                - datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                color_coded= True if color else False
            )
        )

    for project, elements in projects.items():
        click.echo(project)
        for element in elements:
            click.echo(element)
        click.echo()


def get_command(ctx: click.Context, spec: str, color: bool) -> None:
    """ Implementation of the *get* command.
    """

    headers = {"Authorization": f"Bearer {ctx.obj.get_value('token')}"}
    if spec == "issues":
        res = get_issues(headers=headers)
        print_issues(res, color)
    elif spec == "prs":
        res = get_prs(ctx, headers=headers)
        print_prs(res, color)
    elif spec == "all":
        res = get_issues(headers=headers)
        print_issues(res, color)
        click.echo(f"* " * 20)
        res = get_prs(ctx, headers=headers)
        print_prs(res, color)
    else:
        raise click.BadArgumentUsage(message=f"Unkown spec: {spec}")

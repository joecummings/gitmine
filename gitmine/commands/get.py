import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, List, Mapping

import click
import requests

from gitmine.constants import LOGGER
from gitmine.utils import catch_bad_responses

logger = logging.getLogger(LOGGER)


class GithubElement:
    """ Container for Github Issue or Pull Request.
    """

    def __init__(
        self,
        type: str,
        title: str,
        number: int,
        url: str,
        elapsed_time: timedelta,
        color_coded: bool,
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

        if self.elapsed_time < timedelta(days=2):
            return "green"
        if self.elapsed_time < timedelta(days=5):
            return "yellow"
        return "red"


class Issue(GithubElement):
    """ Github Issue
    """

    def __init__(
        self,
        title: str,
        number: int,
        url: str,
        elapsed_time: timedelta,
        color_coded: bool,
    ):
        super().__init__(
            type="Issue",
            title=title,
            number=number,
            url=url,
            elapsed_time=elapsed_time,
            color_coded=color_coded,
        )


class PullRequest(GithubElement):
    """ Github Pull Request
    """

    def __init__(
        self,
        title: str,
        number: int,
        url: str,
        elapsed_time: timedelta,
        color_coded: bool,
    ):
        super().__init__(
            type="PullRequest",
            title=title,
            number=number,
            url=url,
            elapsed_time=elapsed_time,
            color_coded=color_coded,
        )


def get_prs(ctx: click.Context, headers: Mapping[str, str]) -> List[Mapping[str, Any]]:
    """ Get all Github PRs assigned to user.
    """
    username = ctx.obj.get_value("username")
    logger.debug(f"Fetching PRs for {username} from github.com \n")
    url_format = f"https://api.github.com/search/issues?q=is:open+is:pr+review-requested:{username}"
    with requests.Session() as s:
        response = s.get(url_format, headers=headers)
    catch_bad_responses(response, get="prs")
    return response.json()["items"]


def print_prs(prs: List[Mapping[str, Any]], color: bool, asc: bool, repo: str) -> None:
    """ Print PRs in the following format:

    repo-title
    #pr-number pr-title
    ...
    """
    if not prs:
        click.echo("No assigned PRs! Keep up the good work.")

    projects = defaultdict(list)

    for pr in prs:
        url = pr["html_url"]
        curr_project = re.findall(r"github.com/(.+?)/pull", url)[0]
        if repo and curr_project != repo:
            continue
        projects[curr_project].append(
            PullRequest(
                title=pr["title"],
                number=pr["number"],
                url=url,
                elapsed_time=datetime.now()
                - datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                color_coded=True if color else False,
            )
        )

    echo_elements(projects, len(prs))


def get_collaborator_repos(headers: Mapping[str, str]) -> Mapping[str, Any]:
    url_format = "https://api.github.com/user/repos"
    params = {"affiliation": "collaborator"}
    response = requests.get(url_format, headers=headers, params=params)
    catch_bad_responses(response, get="issues")
    return response.json()


def get_unassigned_issues(
    asc: bool, headers: Mapping[str, str]
) -> List[Mapping[str, Any]]:
    params = {"direction": "asc" if asc else "desc", "assignee": "none"}
    collaborator_repos = get_collaborator_repos(headers)
    url_format = "https://api.github.com/repos"
    issues = []
    for repo in collaborator_repos:
        # make this multithreaded
        # print(repo["full_name"])
        specific_url_format = f"{url_format}/{repo['full_name']}/issues"
        response = requests.get(specific_url_format, headers=headers, params=params)
        # print(response.json())
        catch_bad_responses(response, get="issues")
        if response.json():
            for issue in response.json():
                issue["repository"] = {"full_name": repo["full_name"]}
                issues.append(issue)
    return issues


def get_issues(
    unassigned: bool, asc: bool, headers: Mapping[str, str]
) -> List[Mapping[str, Any]]:
    """ Get all Github Issues assigned to user.
    """

    if unassigned:
        print("getting unassigned")
        return get_unassigned_issues(asc, headers)

    params = {"direction": "asc"} if asc else {"direction": "desc"}
    logger.debug(f"Fetching issues from github.com \n")
    url_format = "https://api.github.com/issues"
    response = requests.get(url_format, headers=headers, params=params)
    catch_bad_responses(response, get="issues")
    return response.json()


def print_issues(issues: List[Mapping[str, Any]], color: bool, repo: str) -> None:
    """ Print issues in the following format:

    repo-title
    #issue-number issue-title
    ...
    """
    if not issues:
        click.echo("No assigned Issues! Keep up the good work.")

    projects = defaultdict(list)

    for issue in issues:
        curr_project = issue["repository"]["full_name"]
        if repo and curr_project != repo:
            continue
        projects[curr_project].append(
            Issue(
                title=issue["title"],
                number=issue["number"],
                url=issue["html_url"],
                elapsed_time=datetime.now()
                - datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                color_coded=True if color else False,
            )
        )

    echo_elements(projects, len(issues))


def echo_elements(projects: Mapping[str, Any], num_of_issues: int) -> None:
    """ Print to stdout.
    """

    if num_of_issues > 20:
        joined_str = []
        for project, elements in projects.items():
            joined_str.append(project)
            for elem in elements:
                joined_str.append(str(elem))
            joined_str.append("\n")
        join_elements = "\n".join(joined_str)
        click.echo_via_pager(join_elements)
    else:
        for project, elements in projects.items():
            click.echo(project)
            for element in elements:
                click.echo(element)
            click.echo()


def get_command(
    ctx: click.Context, spec: str, color: bool, asc: bool, repo: str, unassigned: bool
) -> None:
    """ Implementation of the *get* command.
    """
    logger.info(
        f"""Getting {spec} for {ctx.obj.get_value('username')}
        from github.com with parameters: color={str(color)}, ascending={str(asc)} \n"""
    )
    headers = {"Authorization": f"Bearer {ctx.obj.get_value('token')}"}
    if spec == "issues":
        res = get_issues(unassigned, asc, headers=headers)
        print_issues(res, color, repo)
    elif spec == "prs":
        res = get_prs(ctx, headers=headers)
        print_prs(res, color, asc, repo)
    elif spec == "all":
        res = get_issues(unassigned, asc, headers=headers)
        print_issues(res, color, repo)
        click.echo(f"* " * 20)
        res = get_prs(ctx, headers=headers)
        print_prs(res, color, asc, repo)
    else:
        raise click.BadArgumentUsage(message=f"Unkown spec: {spec}")

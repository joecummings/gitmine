from collections import defaultdict
import concurrent.futures
from datetime import datetime, timedelta
import logging
import re
import threading
from typing import Any, List, Mapping, Optional

import click
import requests

from gitmine.constants import MAX_ELEMS_TO_STDOUT, OK_DELTA, WARNING_DELTA
from gitmine.endpoints import ISSUES_ENDPOINT, REPOS_ENDPOINT, SEARCH_ENDPOINT, USER_ENDPOINT
from gitmine.utils import catch_bad_responses

logger = logging.getLogger()
thread_local = threading.local()


def get_session() -> Any:
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


class GithubElement:
    """ Container for Github Issue or Pull Request.
    """

    def __init__(
        self,
        name: str,
        title: str,
        number: int,
        url: str,
        elapsed_time: timedelta,
        color_coded: bool,
        labels: Optional[List[Mapping[str, Any]]] = None,
    ) -> None:
        self.name = name
        self.title = title
        self.number = number
        self.url = url
        self.labels = labels
        self.elapsed_time = elapsed_time
        self.color_coded = color_coded

    def __repr__(self) -> str:
        issue_num_with_color = click.style(
            "".join(["#", str(self.number)]), fg=self._elapsed_time_to_color()
        )
        return f"{issue_num_with_color} {self.title} {self._parse_labels_for_repr()}"

    def _elapsed_time_to_color(self) -> str:
        if not self.color_coded:
            return "white"

        if self.elapsed_time < timedelta(days=OK_DELTA):
            return "green"
        if self.elapsed_time < timedelta(days=WARNING_DELTA):
            return "yellow"
        return "red"

    def _parse_labels_for_repr(self) -> str:
        if self.labels:
            label_names = [label["name"] for label in self.labels]
            all_names = ", ".join(label_names)
            if all_names:
                return click.style("".join(["(", all_names, ")"]), fg="green")
        return ""


class Issue(GithubElement):
    """Github Issue"""

    def __init__(
        self,
        title: str,
        number: int,
        labels: List[Mapping[str, Any]],
        url: str,
        elapsed_time: timedelta,
        color_coded: bool,
    ):
        super().__init__(
            name="Issue",
            title=title,
            number=number,
            url=url,
            labels=labels,
            elapsed_time=elapsed_time,
            color_coded=color_coded,
        )


class PullRequest(GithubElement):
    """Github Pull Request"""

    def __init__(
        self, title: str, number: int, url: str, elapsed_time: timedelta, color_coded: bool,
    ):
        super().__init__(
            name="PullRequest",
            title=title,
            number=number,
            url=url,
            elapsed_time=elapsed_time,
            color_coded=color_coded,
        )


class Repository:
    """ Container class for a Github Repository
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.issues: List[Issue] = []
        self.prs: List[PullRequest] = []

    def add_issue(self, issue: Issue) -> None:
        self.issues.append(issue)

    def add_pr(self, pr: PullRequest) -> None:
        self.prs.append(pr)

    def has_issues(self) -> bool:
        return bool(self.issues)

    def has_prs(self) -> bool:
        return bool(self.prs)

    def as_str(self, elem: str) -> str:
        res = [self.name]
        if elem == "issues":
            for issue in self.issues:
                res.append(str(issue))
        elif elem == "prs":
            for pr in self.prs:
                res.append(str(pr))
        return "\n".join(res) + "\n"


class RepoDict(defaultdict):  # type: ignore
    """ Class to extend *defaultdict* to be able to access a key as input
    """

    def __missing__(self, key: str) -> Repository:
        self[key] = Repository(name=key)
        return self[key]  # type: ignore

    def total_num_of_issues(self) -> int:
        return sum(len(r.issues) for r in self.values())

    def total_num_of_prs(self) -> int:
        return sum(len(r.prs) for r in self.values())


def get_prs(ctx: click.Context, color: bool, headers: Mapping[str, str]) -> RepoDict:
    """ Get all Github PRs assigned to user.
    """
    username = ctx.obj.get_value("username")
    logger.debug(f"Fetching PRs for {username} from github.com \n")
    url = SEARCH_ENDPOINT.copy()
    query_params = " ".join(["is:open", "is:pr", f"review-requested:{username}"])
    url.add(path="/issues", args={"q": query_params})
    with requests.Session() as s:
        response = s.get(url, headers=headers)
    catch_bad_responses(response, get="prs")
    prs = response.json()["items"]

    repositories = RepoDict()
    for pr in prs:
        url = pr["html_url"]
        repo_name = re.findall(r"github.com/(.+?)/pull", url)[0]
        repositories[repo_name].add_pr(
            PullRequest(
                title=pr["title"],
                number=pr["number"],
                url=url,
                elapsed_time=datetime.now()
                - datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                color_coded=color,
            )
        )

    return repositories


def get_unassigned_issues(asc: bool, color: bool, headers: Mapping[str, str]) -> RepoDict:
    """ Get all Github Issues that are unnassigned from the repos in which user is a collaborator.
    """

    def get_collaborator_repos() -> Any:
        """ Get all Github repos where user is classified as a collaborator.
        """
        params = {"affiliation": "collaborator"}
        url = USER_ENDPOINT.copy()
        url.path /= "repos"
        response = requests.get(url, headers=headers, params=params)
        catch_bad_responses(response, get="repos")
        return response.json()

    collaborator_repos = get_collaborator_repos()
    params = {"direction": "asc" if asc else "desc", "assignee": "none"}

    def get_issues_by_repo(repo: Mapping[str, Any]) -> Repository:
        """ Get all Github Issues in a repo specified by params.
        """

        session = get_session()
        url = REPOS_ENDPOINT.copy()
        url.path = url.path / repo["full_name"] / "issues"
        with session.get(url, headers=headers, params=params) as response:
            catch_bad_responses(response, get="issues")
            repo_name = repo["full_name"]
            repo_class = Repository(name=repo_name)
            for issue in response.json():
                repo_class.add_issue(
                    Issue(
                        title=issue["title"],
                        number=issue["number"],
                        url=issue["html_url"],
                        labels=issue["labels"],
                        elapsed_time=datetime.now()
                        - datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                        color_coded=color,
                    )
                )
            return repo_class

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        repositories = RepoDict(
            # https://www.gitmemory.com/issue/python/mypy/7217/512213750
            Repository,  # type: ignore
            {
                repo.name: repo
                for repo in filter(
                    lambda x: x.has_issues(), executor.map(get_issues_by_repo, collaborator_repos),
                )
            },
        )

    return repositories


def get_issues(
    unassigned: bool, asc: bool, color: bool, repo_name: str, headers: Mapping[str, str]
) -> RepoDict:
    """ Get all Github Issues assigned to user.
    """

    if unassigned:
        click.echo("Hang on, getting unassigned issues for you...")
        return get_unassigned_issues(asc, color, headers)

    params = {"direction": "asc" if asc else "desc"}
    logger.debug("Fetching issues from github.com \n")
    response = requests.get(ISSUES_ENDPOINT, headers=headers, params=params)
    catch_bad_responses(response, get="issues")

    repositories = RepoDict()
    for issue in response.json():
        repo_name = issue["repository"]["full_name"]
        repositories[repo_name].add_issue(
            Issue(
                title=issue["title"],
                number=issue["number"],
                url=issue["html_url"],
                labels=issue["labels"],
                elapsed_time=datetime.now()
                - datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
                color_coded=color,
            )
        )

    return repositories


def echo_info(repos: RepoDict, elem: str) -> None:
    """ Print issues/prs in the following format:

    repo-title
    #issue-number issue-title
    ...
    #pr-number pr-title
    """

    if not repos:
        click.echo(f"No {elem} found! Keep up the good work.")

    num_of_elems = repos.total_num_of_issues() if elem == "issues" else repos.total_num_of_prs()

    if num_of_elems > MAX_ELEMS_TO_STDOUT:
        all_repos = [repo.as_str(elem) for repo in repos.values()]
        click.echo_via_pager("\n".join(all_repos))
    else:
        for repo in repos.values():
            click.echo(repo.as_str(elem))


def get_command(
    ctx: click.Context,
    spec: str,
    color: bool,
    asc: bool,
    repo_name: str = "",
    unassigned: bool = False,
) -> None:
    """ Implementation of the *get* command.
    """

    logger.info(
        f"""Getting {spec} for {ctx.obj.get_value('username')}
        from github.com with parameters: color={str(color)}, ascending={str(asc)} \n"""
    )
    headers = {"Authorization": f"Bearer {ctx.obj.get_value('token')}"}

    if spec == "all":
        res = get_issues(unassigned, asc, color, repo_name, headers=headers)
        echo_info(res, "issues")
        click.echo("* " * 20)
        res = get_prs(ctx, color, headers=headers)
        echo_info(res, "prs")
    elif spec == "issues":
        res = get_issues(unassigned, asc, color, repo_name, headers=headers)
        echo_info(res, "issues")
    elif spec == "prs":
        res = get_prs(ctx, color, headers=headers)
        echo_info(res, "prs")
    else:
        raise click.BadArgumentUsage(message=f"Unkown spec: {spec}")

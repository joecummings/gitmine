import concurrent.futures
import logging
import re
import threading
from typing import Any, Mapping

import click
import requests

from gitmine.constants import ISSUE, MAX_ELEMS_TO_STDOUT, PULL_REQUEST
from gitmine.endpoints import ISSUES_ENDPOINT, REPOS_ENDPOINT, SEARCH_ENDPOINT, USER_ENDPOINT
from gitmine.models.github_elements import GithubElement, RepoDict, Repository
from gitmine.utils import catch_bad_responses

logger = logging.getLogger()
thread_local = threading.local()


def get_session() -> Any:
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def get_prs(ctx: click.Context, color: bool, headers: Mapping[str, str]) -> RepoDict:
    """Get all Github PRs assigned to user."""
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
            GithubElement.from_dict(pr, elem_type=PULL_REQUEST, color_coded=color)
        )

    return repositories


def get_unassigned_issues(asc: bool, color: bool, headers: Mapping[str, str]) -> RepoDict:
    """Get all Github Issues that are unnassigned from the repos in which user is a collaborator."""

    def get_collaborator_repos() -> Any:
        """Get all Github repos where user is classified as a collaborator."""
        params = {"affiliation": "collaborator"}
        url = USER_ENDPOINT.copy()
        url.path /= "repos"
        response = requests.get(url, headers=headers, params=params)
        catch_bad_responses(response, get="repos")
        return response.json()

    collaborator_repos = get_collaborator_repos()
    params = {"direction": "asc" if asc else "desc", "assignee": "none"}

    def get_issues_by_repo(repo: Mapping[str, Any]) -> Repository:
        """Get all Github Issues in a repo specified by params."""

        session = get_session()
        url = REPOS_ENDPOINT.copy()
        url.path = url.path / repo["full_name"] / "issues"
        with session.get(url, headers=headers, params=params) as response:
            catch_bad_responses(response, get="issues")
            repo_name = repo["full_name"]
            repo_class = Repository(name=repo_name)
            for issue in response.json():
                repo_class.add_issue(
                    GithubElement.from_dict(issue, elem_type=ISSUE, color_coded=color)
                )
            return repo_class

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        repositories = RepoDict(
            # https://www.gitmemory.com/issue/python/mypy/7217/512213750
            Repository,
            {
                repo.name: repo
                for repo in filter(
                    lambda x: x.has_issues(),
                    executor.map(get_issues_by_repo, collaborator_repos),
                )
            },
        )

    return repositories


def get_issues(
    unassigned: bool, asc: bool, color: bool, repo_name: str, headers: Mapping[str, str]
) -> RepoDict:
    """Get all Github Issues assigned to user."""

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
            GithubElement.from_dict(issue, elem_type=ISSUE, color_coded=color)
        )

    return repositories


def echo_info(repos: RepoDict, elem: str) -> None:
    """Print issues/prs in the following format:

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
    """Implementation of the *get* command."""

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

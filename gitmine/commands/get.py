import click
from datetime import datetime, timedelta
from typing import Any, List, Mapping
from gitmine.utils import catch_bad_responses
import requests
from collections import defaultdict


def _elasped_time_to_color(elapsed_time: timedelta) -> str:
    if elapsed_time < timedelta(days=1):
        return "green"
    if elapsed_time < timedelta(days=3):
        return "yellow"
    return "red"


def make_hyperlink(link: str, text: str) -> str:
    """ TODO: actual make this hyperlink
    """
    return text


# @click.pass_context
# def _get_prs(ctx: click.Context, headers: Mapping[str, str]) -> List[Mapping[str, str]]:
#     username = ctx.obj.get_value("username")
#     url_format = f"https://api.github.com/search/issues?q=is:open+is:pr+review-requested:{username}"
#     response = requests.get(url_format, headers=headers)
#     catch_bad_responses(response)
#     return response.json()["items"]

# def _print_prs(prs: List[Mapping[str, str]]) -> None:
#     click.echo("PR Reviews")
#     for i, pr in enumerate(prs):
#         click.echo(pr["number"], color="green")
#         click.echo(
#             f"""
#         {i}: {pr["title"]}
#         - Url: {pr["html_url"]}
#         - Time since creation: {datetime.now() - datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")}
#         """
#         )


def _get_issues(headers: Mapping[str, str]) -> List[Mapping[str, Any]]:
    url_format = "https://api.github.com/issues"
    response = requests.get(url_format, headers=headers)
    catch_bad_responses(response)
    return response.json()


def _print_issues(issues: List[Mapping[str, Any]]) -> None:

    projects = defaultdict(list)

    for issue in issues:

        curr_project = issue["repository"]["full_name"]
        projects[curr_project].append(
            {
                "title": issue["title"],
                "number": issue["number"],
                "url": issue["html_url"],
                "elapsed_time": datetime.now()
                - datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
            }
        )

    for project, issues in projects.items():

        click.echo(project)

        for issue in issues:

            color = _elasped_time_to_color(issue["elapsed_time"])
            formatted_text = make_hyperlink(issue["url"], issue["title"])

            click.echo(
                f"{click.style(''.join(['#', str(issue['number'])]), fg=color)} {formatted_text}"
            )

        click.echo()


def get_command(ctx: click.Context, spec: str) -> None:
    """ Implementation of the *get* command
    """

    headers = {"Authorization": f"Bearer {ctx.obj.get_value('token')}"}
    if spec == "issues":
        res = _get_issues(headers=headers)
        _print_issues(res)
    elif spec == "prs":
        # res = _get_prs(headers=headers)
        # _print_prs(res)
        pass
    elif spec == "all":
        res = _get_issues(headers=headers)
        _print_issues(res)
        click.echo(f"*" * 20)
        # res = _get_prs(headers=headers)
        # _print_prs(res)
    else:
        raise click.BadArgumentUsage(message=f"Unkown spec: {spec}")

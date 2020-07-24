import click
import requests
from datetime import timedelta, datetime, date
from pathlib import Path
from typing import Any, Mapping, Optional, List
from colorama import Fore, Style
from collections import defaultdict

__author__ = "Joe Cummings"

# token = "37c9d559934ae509abbf7548c9dfdf58cbb3d656"
# username = "joecummings"
GITHUB_CREDENTIALS_PATH = Path.home() / Path(".gitmine_credentials")


class GithubConfig:
    """ Github Config object, holds information about username and bearer token
    """

    def _get(self, prop: str) -> str:
        if prop == "token":
            return self.token
        elif prop == "username":
            return self.username
        else:
            raise ValueError(f"Unknown property specified: {prop}")

    def _set(self, prop: str, value: str) -> None:
        if prop == "token":
            self.token = value
        elif prop == "username":
            self.username = value
        else:
            raise ValueError(
                f"Unknown property specified: {prop}"
            )  # replace with click exceptions


def make_hyperlink(link: str, text: str) -> str:
    return text
    # return f"^[]8;;{link}^G{text}^[]8;;^G"


## Add option for asc vs. desc time

## option for interactive

## option for click


@click.group()
@click.pass_context
def gitmine(ctx: click.Context):
    """ Simple CLI for querying assigned Issues and PR reviews from Github
    """
    pass


@gitmine.command()
@click.argument("repo")
@click.argument("number")
@click.pass_context
def go(ctx: click.Context, repo: str, number: Optional[int]) -> None:
    """ Open up a browser page to the issue number in the Github repository specified.

    Args:
        repo: Name of the repository to query
        number: Issue number of the repository to query. If this is left out, will open a page to the main page of the repository.
    """
    url_format = ""
    click.launch()


def _catch_bad_responses(res) -> None:
    res.raise_for_status()


def _elasped_time_to_color(elapsed_time: timedelta) -> str:
    if elapsed_time < timedelta(days=1):
        return "green"
    elif elapsed_time < timedelta(days=3):
        return "yellow"
    return "red"


@click.pass_context
def _get_issues(
    ctx: click.Context, headers: Mapping[str, str]
) -> List[Mapping[str, Any]]:
    url_format = "https://api.github.com/issues"
    response = requests.get(url_format, headers=headers)
    _catch_bad_responses(response)
    return response.json()


def _print_issues(issues: List[Mapping[str, Any]]) -> None:

    projects = defaultdict(list)

    for issue in issues:

        curr_project = issue["repository"]["name"]
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


@click.pass_context
def _get_prs(ctx: click.Context, headers: Mapping[str, str]) -> List[Mapping[str, str]]:
    username = ctx.obj._get("username")
    url_format = f"https://api.github.com/search/issues?q=is:open+is:pr+review-requested:{username}"
    response = requests.get(url_format, headers=headers)
    _catch_bad_responses(response)
    return response.json()["items"]


def _print_prs(prs: List[Mapping[str, str]]) -> None:
    click.echo("PR Reviews")
    for i, pr in enumerate(prs):
        click.echo(pr["number"], color="green")
        click.echo(
            f"""
        {i}: {pr["title"]}
        - Url: {pr["html_url"]}
        - Time since creation: {datetime.now() - datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")}
        """
        )


@gitmine.command()
@click.argument("spec")
@click.pass_context
def get(ctx: click.Context, spec: str) -> None:
    """ Get assigned Github Issues and/or Github PRs.

    Args:
        spec: What information to pull. Can be {issues, prs, all}. 
    """

    headers = {"Authorization": f"Bearer {ctx.obj._get('token')}"}
    if spec == "issues":
        res = _get_issues(headers)
        _print_issues(res)
    elif spec == "prs":
        res = _get_prs(headers)
        _print_prs(res)
    elif spec == "all":
        res = _get_issues(headers)
        _print_issues(res)
        click.echo(f"*" * 20)
        res = _get_prs(headers)
        _print_prs(res)
    else:
        raise ValueError(f"Unknown spec: {spec}")


@gitmine.command()
@click.argument("prop", nargs=1, required=True, type=click.STRING)
@click.argument("value", nargs=1, required=False, type=click.STRING)
@click.pass_context
def config(ctx: click.Context, prop: str, value: str) -> None:
    """ Access Github Config information. Currently, config requires a Github username and Bearer token.

    Args:
        prop: Property to be set if *value* is also provided. If not, will return the current value of *prop* if it exists.
        value: Value of property to be set.
    """

    if not value:
        click.echo(f"{ctx.obj._get(prop)}")
    else:
        with open(GITHUB_CREDENTIALS_PATH, "r") as read_handle:
            props_val = {}
            for line in read_handle:
                curr_prop, curr_value = line.split()
                props_val[curr_prop] = curr_value
            with open(GITHUB_CREDENTIALS_PATH, "w+") as write_handle:
                props_val[prop] = value
                for p, v in props_val.items():
                    write_handle.write(f"{p} {v}\n")

        ctx.obj._set(prop, value)
        click.echo(value)


def get_or_create_github_config() -> GithubConfig:
    """ Get Github Config info if it's already been written to disk, 
        otherwise create an empty config to be filled in later.
    """

    github_config = GithubConfig()

    if GITHUB_CREDENTIALS_PATH.exists():
        with open(GITHUB_CREDENTIALS_PATH, "r") as handle:
            for line in handle:
                prop, value = line.split()
                github_config._set(prop, value)

    return github_config


def main():
    gitmine(obj=get_or_create_github_config())


if __name__ == "__main__":
    main()

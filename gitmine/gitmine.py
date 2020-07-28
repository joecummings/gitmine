from typing import Optional

import click

from gitmine.commands.config import config_command, get_or_create_github_config
from gitmine.commands.get import get_command
from gitmine.commands.go import go_command


@click.group()
@click.pass_context
def gitmine(ctx: click.Context):
    """ Simple CLI for querying assigned Issues and PR reviews from Github.
    """


@gitmine.command()
@click.argument(
    "prop", nargs=1, required=True, type=click.Choice(["username", "token"])
)
@click.argument("value", nargs=1, required=False, type=click.STRING)
@click.pass_context
def config(ctx: click.Context, prop: str, value: str) -> None:
    """ Access Github Config information. Currently, config requires a Github username and Bearer token.

    PROP is the property to be set if *value* is also provided. If not, will return the current value of *prop* if it exists.\n
    VALUE is the value of property to be set.
    """
    config_command(ctx, prop, value)


@gitmine.command()
@click.option(
    "--color/--no-color",
    default=True,
    help="Color code Issues/PRs according to elapsed time.",
)
@click.option(
    "--asc/--desc",
    default=False,
    help="Print Issues/PRs in ascending/descending order of elapsed time",
)
@click.argument(
    "spec", nargs=1, required=True, type=click.Choice(["issues", "prs", "all"])
)
@click.pass_context
def get(ctx: click.Context, spec: str, color: bool, asc: bool) -> None:
    """ Get assigned Github Issues and/or Github PRs.

    SPEC is what information to pull. Can be {issues, prs, all}.
    """
    get_command(ctx, spec, color, asc)


@gitmine.command()
@click.argument("repo", nargs=1, required=True, type=click.STRING)
@click.argument("number", nargs=1, required=False, type=click.INT)
@click.pass_context
def go(ctx: click.Context, repo: str, number: Optional[int]) -> None:
    """ Open up a browser page to the issue number in the Github repository specified.

    REPO is the full name of the repository to query.\n
    NUMBER is the issue number of the repository to query. If this is not provided, will open a page to the main page of the repository.
    """
    go_command(repo, number)


def main():
    gitmine(obj=get_or_create_github_config())


if __name__ == "__main__":
    main()

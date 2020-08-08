from typing import Optional

import click

from gitmine.commands.config import config_command, get_or_create_github_config
from gitmine.commands.get import get_command
from gitmine.commands.go import go_command
from gitmine.utils import set_verbosity


@click.group()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Give more output. Option is additive, and can be used up to three times.",
)
@click.pass_context
def gitmine(ctx: click.Context, verbose: int):
    """ Simple CLI for querying assigned Issues and PR reviews from Github.
    """
    set_verbosity(verbose)
    # Set the context object
    ctx.obj = get_or_create_github_config()


class StdCommand(click.core.Command):
    """
    A base class with common parameters
    Idea pulled from https://stackoverflow.com/questions/40182157/shared-options-and-flags-between-commands
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params.insert(
            0,
            click.core.Option(
                ("-v", "--verbose",),
                count=True,
                help="Give more output. Option is additive, and can be used up to three times.",
            ),
        )


@gitmine.command(cls=StdCommand)
@click.option(
    "--encrypt/--no-encrypt",
    default=False,
    help="Encrypt your credentials. Undo encryption by re-setting the config without the flag.",
)
@click.argument(
    "prop", nargs=1, required=True, type=click.Choice(["username", "token"])
)
@click.argument("value", nargs=1, required=False, type=click.STRING)
@click.pass_context
def config(
    ctx: click.Context, prop: str, value: str, encrypt: bool, verbose: int
) -> None:
    """ Set or Access Github Config information. Currently, config requires a Github username and Bearer token.

    [username|token] is the property to be set if *value* is also provided. If not, will return the current value of *prop* if it exists.\n
    VALUE is the value of property to be set.
    """
    set_verbosity(verbose)
    config_command(ctx, prop, value, encrypt)


@gitmine.command(cls=StdCommand)
@click.option(
    "--color/--no-color",
    default=True,
    help="Color code Issues/PRs according to elapsed time.",
)
@click.option(
    "--asc/--desc",
    default=False,
    help="Print Issues/PRs in ascending/descending order of elapsed time.",
)
@click.option("--repo", help="Specify a repo from which to get Issues / PRs.")
@click.argument(
    "spec", nargs=1, required=True, type=click.Choice(["issues", "prs", "all"])
)
@click.pass_context
def get(
    ctx: click.Context, spec: str, color: bool, asc: bool, repo: str, verbose: int
) -> None:
    """ Get assigned Github Issues and/or Github PRs.

    [issues|prs|all] is what information to pull. Can be {issues, prs, all}.
    """
    set_verbosity(verbose)
    get_command(ctx, spec, color, asc, repo)


@gitmine.command(cls=StdCommand)
@click.argument("repo", nargs=1, required=True, type=click.STRING)
@click.argument("number", nargs=1, required=False, type=click.INT)
@click.pass_context
def go(ctx: click.Context, repo: str, number: Optional[int], verbose: int) -> None:
    """ Open a browser page for the given repositiory / issue.

    REPO is the full name of the repository to query.\n
    NUMBER is the issue number of the repository to query. If this is not provided, will open a page to the main page of the repository.
    """
    set_verbosity(verbose)
    go_command(repo, number)


def main():
    gitmine(obj={})


if __name__ == "__main__":
    main()

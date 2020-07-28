import click
from pathlib import Path

from gitmine.constants import GITHUB_CREDENTIALS_PATH


class GithubConfig:
    """ Github Config object, holds information about username and bearer token
    """

    def __init__(self):
        self.token = None
        self.username = None

    def get_value(self, prop: str) -> str:
        if prop == "token":
            return self.token
        if prop == "username":
            return self.username
        raise click.BadArgumentUsage(message=f"Unknown property specified: {prop}")

    def set_prop(self, prop: str, value: str) -> None:
        if prop == "token":
            self.token = value
        elif prop == "username":
            self.username = value
        else:
            raise click.BadArgumentUsage(message=f"Unknown property specified: {prop}")


def config_command(ctx: click.Context, prop: str, value: str) -> None:
    """ Implementation of the *config* command
    """

    if not value:
        click.echo(ctx.obj.get_value(prop))
    else:
        ctx.obj.set_prop(prop, value)

        with open(GITHUB_CREDENTIALS_PATH, "r") as read_handle:
            props_val = {}
            for line in read_handle:
                curr_prop, curr_value = line.split()
                props_val[curr_prop] = curr_value
            with open(GITHUB_CREDENTIALS_PATH, "w+") as write_handle:
                props_val[prop] = value
                for true_prop, true_value in props_val.items():
                    write_handle.write(f"{true_prop} {true_value}\n")

        click.echo(value)


def get_or_create_github_config() -> GithubConfig:
    """ Get Github Config info if it's already been written to disk,
        otherwise create an empty config to be filled in later.
        Create a credentials folder if it does not exist
    """

    github_config = GithubConfig()

    if GITHUB_CREDENTIALS_PATH.exists():
        with open(GITHUB_CREDENTIALS_PATH, "r") as handle:
            for line in handle:
                prop, value = line.split()
                github_config.set_prop(prop, value)
    else:
        GITHUB_CREDENTIALS_PATH.touch()

    return github_config

import logging
from pathlib import Path
from typing import Dict, Optional

import click
import yaml

from gitmine.constants import GH_CREDENTIALS_PATH, GHP_CREDENTIALS_DIR, GHP_CREDENTIALS_PATH

logger = logging.getLogger()


class GithubConfig:
    """ Github Config object, holds information about username and bearer token
    """

    def __init__(self) -> None:
        self.token = ""
        self.username = ""

    def get_value(self, prop: str) -> Optional[str]:
        if prop == "token":
            return self.token
        elif prop == "username":
            return self.username
        raise click.BadArgumentUsage(message=f"Unknown property specified: {prop}")

    def set_prop(self, prop: str, value: str) -> None:
        if prop == "token":
            self.token = value
        elif prop == "username":
            self.username = value
        else:
            raise click.BadArgumentUsage(message=f"Unknown property specified: {prop}")

    def config_as_dict(self) -> Dict[str, Dict[str, str]]:
        return {"github.com": {"username": self.username, "token": self.token}}

    @staticmethod
    def load_config_from_yaml(path_to_yaml_file: Path) -> "GithubConfig":
        with open(path_to_yaml_file, "r") as handle:
            gh_yaml = yaml.load(handle, Loader=yaml.FullLoader)
            github_config = GithubConfig()

            if gh_yaml:
                gh_yaml_github = gh_yaml["github.com"]
                try:
                    username = gh_yaml_github["username"]
                    token = gh_yaml_github["token"]
                except KeyError:
                    # Copying from GH credentials
                    username = gh_yaml_github["user"]
                    token = gh_yaml_github["oauth_token"]

                github_config.set_prop("username", username)
                github_config.set_prop("token", token)

        return github_config


def config_command(ctx: click.Context, prop: str, value: str) -> None:
    """ Implementation of the *config* command
    """
    if not value and prop:
        click.echo(ctx.obj.get_value(prop))

    elif value:
        ctx.obj.set_prop(prop, value)

        if not GHP_CREDENTIALS_PATH.exists():
            GHP_CREDENTIALS_PATH.touch()

        ghp_config = GithubConfig.load_config_from_yaml(GHP_CREDENTIALS_PATH)
        ghp_config.set_prop(prop, value)
        set_config(ghp_config.config_as_dict())

        logger.info(f"Config {prop} {value} written at {GHP_CREDENTIALS_PATH}")
        click.echo(value)


def set_config(config_dict: Dict[str, Dict[str, str]]) -> None:
    """ Set config file based on dictionary of config values.
    """
    with open(GHP_CREDENTIALS_PATH, "w+") as handle:
        yaml.dump(config_dict, handle)


def get_or_create_github_config() -> GithubConfig:
    """ Get Github Config info if it's already been written to disk,
        otherwise create an empty config to be filled in later.
        Create a credentials folder if it does not exist.
    """
    if not GHP_CREDENTIALS_DIR.exists():
        GHP_CREDENTIALS_DIR.mkdir(parents=True)

    if GHP_CREDENTIALS_PATH.exists():
        return GithubConfig.load_config_from_yaml(GHP_CREDENTIALS_PATH)
    elif GH_CREDENTIALS_PATH.exists():
        gh_config = GithubConfig.load_config_from_yaml(GH_CREDENTIALS_PATH)
        set_config(gh_config.config_as_dict())  # copy to our own credentials
        return gh_config

    return GithubConfig()

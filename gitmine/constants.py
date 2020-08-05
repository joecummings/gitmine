from pathlib import Path

GITHUB_CREDENTIALS_PATH = Path.home() / Path(".gitmine_credentials")
KEY_PATH = Path.cwd() / Path("gitmine.key")

LOGGER_PATH = Path.cwd() / Path("logging.conf")
LOGGER = "gitmine"

VERBOSE_MAP = {
    1: "ERROR",
    2: "INFO",
    3: "DEBUG"
}
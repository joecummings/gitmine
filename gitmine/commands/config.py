import binascii
import logging
from pathlib import Path
from types import TracebackType
from typing import IO, Optional, Type

import click
from cryptography.fernet import Fernet, InvalidToken

from gitmine.constants import GITHUB_CREDENTIALS_PATH, KEY_PATH

logger = logging.getLogger()


class GithubConfig:
    """ Github Config object, holds information about username and bearer token
    """

    def __init__(self) -> None:
        self.token = ""
        self.username = ""
        self.key = ""

    def get_value(self, prop: str) -> Optional[str]:
        if prop == "key":
            return self.key
        elif prop == "token":
            return self.token
        elif prop == "username":
            return self.username
        raise click.BadArgumentUsage(message=f"Unknown property specified: {prop}")

    def set_prop(self, prop: str, value: str) -> None:
        if prop == "key":
            self.key = value
        elif prop == "token":
            self.token = value
        elif prop == "username":
            self.username = value
        else:
            raise click.BadArgumentUsage(message=f"Unknown property specified: {prop}")


def config_command(ctx: click.Context, prop: str, value: str, encrypt: bool, decrypt: bool) -> None:
    """ Implementation of the *config* command
    """
    handle_encrypt_option(encrypt, decrypt)

    if not value and prop:
        click.echo(ctx.obj.get_value(prop))

    elif value:
        ctx.obj.set_prop(prop, value)

        with OpenCredentials("r") as read_handle:
            props_val = {}
            for line in read_handle:
                curr_prop, curr_value = line.split()
                props_val[curr_prop] = curr_value
            with OpenCredentials("w+") as write_handle:
                props_val[prop] = value
                for true_prop, true_value in props_val.items():
                    write_handle.write(f"{true_prop} {true_value}\n")

        logger.info(f"Config {prop} {value} written at {GITHUB_CREDENTIALS_PATH}")
        click.echo(value)


def get_or_create_github_config() -> GithubConfig:
    """ Get Github Config info if it's already been written to disk,
        otherwise create an empty config to be filled in later.
        If a key has been stored locally then the file is encrypted
        Create a credentials folder if it does not exist.
    """
    github_config = GithubConfig()

    logger.info("Found github credentials - loading into Config")
    with OpenCredentials("r") as cred_handle:
        for line in cred_handle:
            prop, value = line.split()
            github_config.set_prop(prop, value)

    return github_config


class OpenCredentials:
    def __init__(self, method: str):
        self.file_name = GITHUB_CREDENTIALS_PATH
        if not self.file_name.exists():
            self.file_name.touch()
        self.method = method
        self.key_exists = KEY_PATH.exists()
        if self.key_exists:
            with open(KEY_PATH, "rb") as key_handle:
                self.key = key_handle.read()
            decrypt_file(self.key, self.file_name)

    def __enter__(self) -> IO[str]:
        self.file_obj = open(  # pylint: disable=attribute-defined-outside-init
            self.file_name, self.method
        )
        if len(self.file_obj.read().split()) == 1 and not self.key_exists:
            raise click.FileError(
                "MissingKey: Credentials file is currently encrypted and the key is missing, please try resetting your credentials file."
            )
        # reset file pointer
        self.file_obj.seek(0)
        return self.file_obj

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        if self.key_exists:
            encrypt_file(self.key, self.file_name)
        self.file_obj.close()
        return True


def handle_encrypt_option(encrypt: bool, decrypt: bool) -> None:
    """Encryption can be True or False as specified by the user parameter:
        True: we generate a key and encrypt the credentials file using Fernet Encryption
        False: if the file is currently encrypted - we decrypt it and delete the key
        None: return
    """

    key_exists = KEY_PATH.exists()
    if key_exists:
        with open(KEY_PATH, "rb") as read_handle:
            key = read_handle.read()

    # Encrypt the file
    if encrypt:
        if not key_exists:
            key = Fernet.generate_key()
            with open(KEY_PATH, "wb") as write_handle:
                write_handle.write(key)
            logger.debug(f"Generated encryption key, stored at {KEY_PATH}")
        encrypt_file(key, GITHUB_CREDENTIALS_PATH)

    # Decrypt the file
    if decrypt:
        if not key_exists:
            raise click.BadOptionUsage(
                option_name="--decrypt", message="cannot be used when file is already decrypted",
            )
        decrypt_file(key, GITHUB_CREDENTIALS_PATH)
        KEY_PATH.unlink()


def encrypt_file(key: bytes, file: Path) -> None:
    """Uses Fernet encryption to encrypt the file at the given path using the key
    """
    if not file.exists():
        logger.info(f"Could not find file {file}")
        return

    try:
        f = Fernet(key)
    except (binascii.Error, ValueError):
        raise click.ClickException(
            "Error: Cannot Encrypt File - given key is in incorrect format, please try resetting your credentials."
        )

    with open(file, "r") as read_handle:
        data = read_handle.read().encode()

    with open(file, "wb") as write_handle:
        try:
            write_handle.write(f.encrypt(data))
        except InvalidToken:
            raise Exception(
                "InvalidKey: could not open your credentials file. Please try setting your credentials again."
            )
    logger.debug(f"Successfully encrypted file {file}")


def decrypt_file(key: bytes, file: Path) -> None:
    """Uses Fernet encryption to decrypt the given file with the corresponding key
        Returns plaintext
    """
    if not file.exists():
        logger.info(f"Could not find file {file}")
        return

    try:
        f = Fernet(key)
    except (binascii.Error, ValueError):
        raise click.ClickException(
            "Error: Cannot Decrypt File - given key is in incorrect format, please try resetting your credentials."
        )

    with open(file, "rb") as read_handle:
        data = read_handle.read()

    with open(file, "w") as write_handle:
        try:
            write_handle.write(f.decrypt(data).decode("UTF-8"))
        except InvalidToken:
            raise Exception(
                "InvalidKey: could not open your credentials file. Please try resetting your credentials."
            )
    logger.debug(f"Successfully decrypted file {file}")

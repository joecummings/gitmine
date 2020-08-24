import base64
import binascii
import logging
import os
from contextlib import contextmanager
from copy import copy
from pathlib import Path
from typing import Union

import click
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from gitmine.constants import GITHUB_CREDENTIALS_PATH, KEY_PATH, LOGGER

logger = logging.getLogger(LOGGER)


class GithubConfig:
    """ Github Config object, holds information about username and bearer token
    """

    def __init__(self):
        self.token = None
        self.username = None
        self.key = None

    def get_value(self, prop: str) -> str:
        if prop == "key":
            return self.key
        elif prop == "token":
            return self.token
        elif prop == "username":
            return self.username
        raise click.BadArgumentUsage(message=f"Unknown property specified: {prop}")

    def get_protected_value(self, prop: str) -> str:
        if prop == "token":
            if self.key:
                return base64.b64encode(os.urandom(len(self.token))).decode("utf-8")
            return self.token
        elif prop == "username":
            return self.username
        raise click.BadArgumentUsage(message=f"Unknown property specified: {prop}")

    def set_prop(self, prop: str, value: Union[str, bytes]) -> None:
        if prop == "key":
            self.key = value
        elif prop == "token":
            self.token = value
        elif prop == "username":
            self.username = value
        else:
            raise click.BadArgumentUsage(message=f"Unknown property specified: {prop}")


def config_command(
    ctx: click.Context, prop: str, value: str, encrypt: bool, decrypt: bool
) -> None:
    """ Implementation of the *config* command
    """
    handle_encrypt_option(encrypt, decrypt)

    if not value and prop:
        click.echo(ctx.obj.get_protected_value(prop))

    elif value:
        ctx.obj.set_prop(prop, value)

        with open_credentials("r") as read_handle:
            props_val = {}
            for line in read_handle:
                curr_prop, curr_value = line.split()
                props_val[curr_prop] = curr_value
            with open_credentials("w+") as write_handle:
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
    with open_credentials("r", config=github_config) as cred_handle:
        for line in cred_handle:
            prop, value = line.split()
            github_config.set_prop(prop, value)

    return github_config


class open_credentials(object):
    def __init__(self, method: str, config=None):
        self.file_name = GITHUB_CREDENTIALS_PATH
        if not self.file_name.exists():
            self.file_name.touch()
        self.method = method
        self.key_exists = KEY_PATH.exists()
        if self.key_exists:
            with open(KEY_PATH, "rb") as key_handle:
                self.key = key_handle.read()
                if config:
                    config.set_prop("key", self.key)
            decrypt_file(self.key, self.file_name)

    def __enter__(self):
        self.file_obj = open(self.file_name, self.method)
        if len(self.file_obj.read().split()) == 1 and not self.key_exists:
            raise click.FileError(
                f"MissingKey: Credentials file is currently encrypted and the key is missing, please try resetting your credentials file"
            )
        # reset file pointer
        self.file_obj.seek(0)
        return self.file_obj

    def __exit__(self, type, value, traceback):
        if self.key_exists:
            encrypt_file(self.key, self.file_name)
        self.file_obj.close()


def handle_encrypt_option(e: bool, d: bool):
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
    if e:
        if not key_exists:
            key = Fernet.generate_key()
            with open(KEY_PATH, "wb") as write_handle:
                write_handle.write(key)
            logger.debug(f"Generated encryption key, stored at {KEY_PATH}")
        encrypt_file(key, GITHUB_CREDENTIALS_PATH)

    # Decrypt the file
    if d:
        if not key_exists:
            raise click.BadOptionUsage(
                option_name="--decrypt",
                message="cannot be used when file is already decrypted",
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
            f"Error: Cannot Encrypt File - given key is in incorrect format, please try resetting your credentials"
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
            f"Error: Cannot Decrypt File - given key is in incorrect format, please try resetting your credentials"
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

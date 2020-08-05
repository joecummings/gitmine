import base64
import logging
import os
from pathlib import Path

import click
from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidKey

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
        if prop == "token":
            return self.token
        if prop == "username":
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


def config_command(ctx: click.Context, prop: str, value: str, e: bool) -> None:
    """ Implementation of the *config* command
    """

    if not value:
        click.echo(ctx.obj.get_value(prop))
    else:

        # No key already exists - generate a new one
        key = ctx.obj.get_value("key")
        if key:
            decrypt_file(key, GITHUB_CREDENTIALS_PATH)
        if e and not key:
            key = generate_key()
        # Special case that a key file exists but we don't want encryption anymore
        elif key and not e:
            KEY_PATH.unlink()

        ctx.obj.set_prop(prop, value)

        with open(GITHUB_CREDENTIALS_PATH, "rb") as read_handle:
            props_val = {}
            for line in read_handle:
                curr_prop, curr_value = line.split()
                props_val[curr_prop.decode()] = curr_value.decode()
            with open(GITHUB_CREDENTIALS_PATH, "wb+") as write_handle:
                props_val[prop] = value
                for true_prop, true_value in props_val.items():
                    write_handle.write(f"{true_prop} {true_value}\n".encode())

        if e:
            encrypt_file(key, GITHUB_CREDENTIALS_PATH)

        logger.info(f"Config {prop} {value} written at {GITHUB_CREDENTIALS_PATH}")
        click.echo(value)


def get_or_create_github_config() -> GithubConfig:
    """ Get Github Config info if it's already been written to disk,
        otherwise create an empty config to be filled in later.
        If a key has been stored locally then the file is encrypted
        Create a credentials folder if it does not exist.
    """
    github_config = GithubConfig()

    key_exists = KEY_PATH.exists()
    if key_exists:
        with open(KEY_PATH, "rb") as handle:
            key = handle.read()
            github_config.set_prop("key", key)
            decrypt_file(key, GITHUB_CREDENTIALS_PATH)
                

    if GITHUB_CREDENTIALS_PATH.exists():
        logger.info("Found github credentials - loading from file")
        with open(GITHUB_CREDENTIALS_PATH, "r") as handle:
            for line in handle:
                prop, value = line.split()
                github_config.set_prop(prop, value)
    else:
        GITHUB_CREDENTIALS_PATH.touch()

    if key_exists:
        encrypt_file(key, GITHUB_CREDENTIALS_PATH)

    return github_config


def generate_key() -> str:
    """Creates an encryption using the given token
       Saves the key to a local file
    """
    key = Fernet.generate_key()

    with open(KEY_PATH, "wb") as handle:
        handle.write(key)

    logger.debug(f"Generated encryption key {key}, stored at {KEY_PATH}")
    return key


def encrypt_file(key: str, file: Path) -> str:
    """Uses Fernet encryption to encrypt the file at the given path using the key
    """
    if not file.exists():
        logger.info(f"Could not find file {file}")
        return
    with open(file, "r") as read_handle:
        data = read_handle.read().encode()
    f = Fernet(key)
    with open(file, "wb") as write_handle:
        try:
            write_handle.write(f.encrypt(data))
        except InvalidKey:
            raise Exception(
                "InvalidKey: could not open your credentials file. Please try setting your credentials again."
            )
    logging.debug(f"Successfully encrypted file {file}")


def decrypt_file(key: str, file: Path) -> str:
    """Uses Fernet encryption to decrypt the given file with the corresponding key
        Returns plaintext
    """
    if not file.exists():
        logger.info(f"Could not find file {file}")
        return
    with open(file, "rb") as read_handle:
        data = read_handle.read()
    f = Fernet(key)
    with open(file, "w") as write_handle:
        try:
            write_handle.write(f.decrypt(data).decode("UTF-8"))
        except InvalidKey:
            raise Exception(
                "InvalidKey: could not open your credentials file. Please try setting your credentials again."
            )
    logger.debug(f"Successfully decrypted file {file}")

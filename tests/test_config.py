import shutil

import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet
from test_constants import GITHUB_CREDENTIALS_PATH_COPY, KEY_PATH_COPY

from gitmine.commands.config import (decrypt_file, encrypt_file, generate_key,
                                     get_or_create_github_config)
from gitmine.constants import GITHUB_CREDENTIALS_PATH, KEY_PATH
from gitmine.gitmine import gitmine

runner = CliRunner()

# CONFIG
@pytest.fixture(scope="module")
def file_config():
    """
    This fixture allows us to keep the credentials
    """
    print("FIXTURE")
    shutil.move(GITHUB_CREDENTIALS_PATH, GITHUB_CREDENTIALS_PATH_COPY)
    key_flag = KEY_PATH.exists()
    if key_flag:
        shutil.move(KEY_PATH, KEY_PATH_COPY)
    yield
    #GITHUB_CREDENTIALS_PATH.unlink()
    KEY_PATH.unlink()
    shutil.move(GITHUB_CREDENTIALS_PATH_COPY, GITHUB_CREDENTIALS_PATH)
    if key_flag:
        shutil.move(KEY_PATH_COPY, KEY_PATH)


def base_runner(options):
    command = ["config"]
    command.extend(options)
    return runner.invoke(gitmine, command)


def test_config_none(file_config):
    result = base_runner([""])
    assert result.exit_code == 2


def test_config_username_returns_specified(file_config):
    result = base_runner(["username"])
    assert result.output == "\n"


def test_config_username_returns_correct(file_config):
    result = base_runner(["username", "abc"])
    print(result)
    assert result.output == "abc\n"


def test_config_token_returns_specified(file_config):
    result = base_runner(["token"])
    assert result.output == "\n"


def test_config_token_returns_correct(file_config):
    result = base_runner(["token", "abcdefg"])
    assert result.output == "abcdefg\n"


def test_config_bad_prop_errors(file_config):
    result = base_runner(["banana-boat"])
    assert result.exit_code == 2  # should fail


def test_config_option_encrypt_key(file_config):
    base_runner(["username", "abc", "--encrypt"])
    assert KEY_PATH.exists()


def test_config_option_encrypt_nokey(file_config):
    base_runner(["username", "abc", "--no-encrypt"])
    assert not KEY_PATH.exists()


def test_config_option_encrypt_correct(file_config):
    name = "abc"
    base_runner(["username", name, "--encrypt"])
    with open(KEY_PATH, "rb") as key_handle:
        key = key_handle.read()
    f = Fernet(key)
    with open(GITHUB_CREDENTIALS_PATH, "rb") as cred_handle:
        data = cred_handle.read()
        decrypted = f.decrypt(data).decode("UTF-8").split("\n")[0]
        prop, d_name = decrypted.split()

    assert name == d_name


def test_config_option_encrypt_invalidKey(file_config):
    token = "abcdefg"
    base_runner(["token", token, "--encrypt"])
    # Generate new key and delete key file
    new_key = Fernet.generate_key()
    with pytest.raises(Exception, match=r"InvalidKey:.*"):
        decrypt_file(new_key, GITHUB_CREDENTIALS_PATH)


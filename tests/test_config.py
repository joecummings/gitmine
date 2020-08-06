import shutil

import pytest
from click.testing import CliRunner
from cryptography.fernet import Fernet

from gitmine.commands.config import (decrypt_file, encrypt_file, generate_key,
                                     get_or_create_github_config)
from gitmine.constants import GITHUB_CREDENTIALS_PATH, KEY_PATH
from gitmine.gitmine import gitmine
from test_constants import TEST_GITHUB_CREDENTIALS_PATH, TEST_KEY_PATH

runner = CliRunner()

# CONFIG
@pytest.fixture
def file_configuration():
    """
    This fixture allows us to keep the credentials
    """
    copy_path = GITHUB_CREDENTIALS_PATH.with_suffix(".copy")
    shutil.copyfile(GITHUB_CREDENTIALS_PATH, copy_path)
    GITHUB_CREDENTIALS_PATH.unlink()
    key_flag = KEY_PATH.exists()
    if key_flag:
        key_copy_path = KEY_PATH.with_suffix(".copy")
        shutil.copyfile(KEY_PATH, key_copy_path)
        KEY_PATH.unlink()
    yield
    GITHUB_CREDENTIALS_PATH.unlink()
    shutil.copyfile(copy_path, GITHUB_CREDENTIALS_PATH)
    if key_flag:
        shutil.copyfile(key_copy_path, KEY_PATH)
        key_copy_path.unlink()


def base_runner(options):
    command = ["config"]
    command.extend(options)
    return runner.invoke(gitmine, command)


def test_config_none():
    result = base_runner([""])
    assert result.exit_code == 2


def test_config_username_returns_specified():
    result = base_runner(["username"])
    assert result.output == "\n"


def test_config_username_returns_correct():
    result = base_runner(["username", "abc"])
    print(result)
    assert result.output == "abc\n"


def test_config_token_returns_specified():
    result = base_runner(["token"])
    assert result.output == "\n"


def test_config_token_returns_correct():
    result = base_runner(["token", "abcdefg"])
    assert result.output == "abcdefg\n"


def test_config_bad_prop_errors():
    result = base_runner(["banana-boat"])
    assert result.exit_code == 2  # should fail


def test_config_option_encrypt_key():
    base_runner(["username", "abc", "--encrypt"])
    assert KEY_PATH.exists()


def test_config_option_encrypt_nokey():
    base_runner(["username", "abc", "--no-encrypt"])
    assert not KEY_PATH.exists()


def test_config_option_encrypt_correct():
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


def test_config_option_encrypt_invalidKey():
    token = "abcdefg"
    base_runner(["token", token, "--encrypt"])
    # Generate new key and delete key file
    new_key = Fernet.generate_key()
    with pytest.raises(Exception, match=r"InvalidKey:.*"):
        decrypt_file(new_key, GITHUB_CREDENTIALS_PATH)

import re
from setuptools import setup


version = "0.0.1"


with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name = "gitmine",
    packages = ["gitmine"],
    entry_points = {
        "console_scripts": ['gitmine = gitmine.gitmine:main']
        },
    install_requires=[
        "click"
    ],
    version = version,
    description = "Simple CLI for querying assigned Issues and PRs from Github.",
    long_description = long_descr,
    author = "Joe Cummings",
    author_email = "jrcummings27@gmail.com",
    )
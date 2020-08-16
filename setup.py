import re

from setuptools import find_packages, setup

version = "0.0.8"


long_descr = open("README.md").read()

with open("requirements.txt", encoding="utf-8") as f:
    all_reqs = f.read().split("\n")

install_requires = [
    x.strip()
    for x in all_reqs
    if ("git+" not in x) and (not x.startswith("#")) and (not x.startswith("-"))
]

setup(
    name="gitmine",
    packages=find_packages(),
    entry_points={"console_scripts": ["gitmine = gitmine.gitmine:main"]},
    install_requires=install_requires,
    include_package_data=True,
    python_requires=">=3.6",
    version=version,
    license="MIT",
    url="https://github.com/joecummings/gitmine",
    description="Simple command-line app for querying assigned Issues and PRs from Github.",
    long_description=long_descr,
    long_description_content_type="text/markdown",
    author="Joe Cummings, Alexis Baudron",
    author_email="jrcummings27@gmail.com",
)

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, List, Mapping, Optional

import click

from gitmine.constants import OK_DELTA, WARNING_DELTA


class GithubElement:
    """Container for Github Issue or Pull Request."""

    def __init__(
        self,
        elem_type: str,
        title: str,
        number: int,
        url: str,
        created_at: datetime,
        color_coded: bool,
        labels: Optional[List[Mapping[str, Any]]] = None,
    ) -> None:
        self.elem_type = elem_type
        self.title = title
        self.number = number
        self.url = url
        self.labels = labels
        self.created_at = created_at
        self.color_coded = color_coded

    def get_formatted_args_for_table(self) -> List[Optional[str]]:
        issue_num_with_color = click.style(
            "".join(["#", str(self.number)]),
            fg=self._elapsed_time_to_color(self._get_elapsed_time()),
        )
        return [issue_num_with_color, self.title, self._parse_labels_for_repr()]

    def _elapsed_time_to_color(self, time: timedelta) -> str:
        if not self.color_coded:
            return "white"

        if time < timedelta(days=OK_DELTA):
            return "green"
        if time < timedelta(days=WARNING_DELTA):
            return "yellow"
        return "red"

    def _parse_labels_for_repr(self) -> str:
        if self.labels:
            label_names = [label["name"] for label in self.labels]
            all_names = ", ".join(label_names)
            if all_names:
                return str(click.style("".join(["(", all_names, ")"]), fg="cyan"))
        return ""

    def _get_elapsed_time(self) -> timedelta:
        return datetime.now() - self.created_at

    @classmethod
    def from_dict(
        cls, obj: Mapping[str, Any], *, elem_type: str, color_coded: bool = False
    ) -> "GithubElement":
        return cls(
            elem_type=elem_type,
            title=obj["title"],
            number=obj["number"],
            labels=obj["labels"],
            url=obj["html_url"],
            created_at=datetime.strptime(obj["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
            color_coded=color_coded,
        )


class Repository:
    """Container class for a Github Repository"""

    def __init__(self, name: str) -> None:
        self.name = name
        self.issues: List[GithubElement] = []
        self.prs: List[GithubElement] = []

    def add_issue(self, issue: GithubElement) -> None:
        self.issues.append(issue)

    def add_pr(self, pr: GithubElement) -> None:
        self.prs.append(pr)

    def has_issues(self) -> bool:
        return bool(self.issues)

    def has_prs(self) -> bool:
        return bool(self.prs)

    def format_for_table(self, elem: str) -> List[List[Optional[str]]]:
        res = list([["***", self.name, None]])
        if elem == "issues":
            for issue in self.issues:
                res.append(issue.get_formatted_args_for_table())
        elif elem == "prs":
            for pr in self.prs:
                res.append(pr.get_formatted_args_for_table())
        # Append row of None's for space between Repos
        res.append([None, None, None])
        return res


class RepoDict(defaultdict):  # type: ignore
    """Class to extend *defaultdict* to be able to access a key as input"""

    def __missing__(self, key: str) -> Repository:
        self[key] = Repository(name=key)
        return self[key]  # type: ignore

    def total_num_of_issues(self) -> int:
        return sum(len(r.issues) for r in self.values())

    def total_num_of_prs(self) -> int:
        return sum(len(r.prs) for r in self.values())

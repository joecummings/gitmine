from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, List, Mapping, Optional

import click

from gitmine.constants import (
    DANGER_DELTA_COLOR,
    ELEM_NUM_COLOR,
    LABELS_COLOR,
    OK_DELTA,
    OK_DELTA_COLOR,
    REPO_NAME_COLOR,
    WARNING_DELTA,
    WARNING_DELTA_COLOR,
)


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
        """Format arguments for Tabulate table.

        Returns:
            List comprised of Issue/PR number, name, labels, and date
        """
        issue_num_with_color = click.style(f"#{self.number}", fg=ELEM_NUM_COLOR)

        date = click.style(
            f"{self._get_elapsed_time().days} days ago",
            fg=self._elapsed_time_to_color(self._get_elapsed_time()),
            dim=True,
        )
        return [issue_num_with_color, self.title, self._parse_labels_for_repr(), date]

    def _elapsed_time_to_color(self, time: timedelta) -> str:
        """Return a color for how much time has elapsed since the Issue/PR was opened.

        Depends on the colors specified by OK_DELTA, WARNING_DELTA, and DANGER_DELTA.
        """
        if not self.color_coded:
            return "white"

        if time < timedelta(days=OK_DELTA):
            return OK_DELTA_COLOR
        if time < timedelta(days=WARNING_DELTA):
            return WARNING_DELTA_COLOR
        return DANGER_DELTA_COLOR

    def _parse_labels_for_repr(self) -> str:
        """Parses Issue/PR labels as one string in parens."""
        if self.labels:
            label_names = [label["name"] for label in self.labels]
            all_names = ", ".join(label_names)
            if all_names:
                return str(click.style(f"({all_names})", fg=LABELS_COLOR, dim=True))
        return ""

    def _get_elapsed_time(self) -> timedelta:
        return datetime.now() - self.created_at

    @classmethod
    def from_dict(
        cls, obj: Mapping[str, Any], *, elem_type: str, color_coded: bool = False
    ) -> "GithubElement":
        """Creates a GithubElement from a JSON Github API response."""
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
        res = list([[None, click.style(self.name, fg=REPO_NAME_COLOR, bold=True), None]])
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
    """Extends *defaultdict* to be able to access a key as input"""

    def __missing__(self, key: str) -> Repository:
        self[key] = Repository(name=key)
        return self[key]  # type: ignore

    def total_num_of_issues(self) -> int:
        return sum(len(r.issues) for r in self.values())

    def total_num_of_prs(self) -> int:
        return sum(len(r.prs) for r in self.values())

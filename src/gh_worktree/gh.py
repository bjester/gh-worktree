from functools import cached_property
import json
import subprocess
from typing import Union

from gh_worktree.context import Context


class GithubCLI(object):
    def __init__(self, context: Context):
        self.context = context

    def _run(self, *command: str):
        result = subprocess.run(
            ["gh", *command],
            capture_output=True,
            text=True,
            check=True,
            cwd=self.context.cwd,
        )
        return result.stdout.strip()

    def pr_status(self, pr_number: Union[int, str]):
        fields = [
            "number",
            "author",
            "baseRefName",
            "headRefName",
            "headRepository",
            "headRepositoryOwner",
            "state",
            "title",
            "url",
        ]
        output = self._run("pr", "view", "--json", ",".join(fields), pr_number)
        return json.loads(output)

    def repo_status(self):
        fields = [
            "defaultBranchRef",
            "name",
            "owner",
            "url",
            "isPrivate",
        ]
        output = self._run("repo", "view", "--json", ",".join(fields))
        return json.loads(output)

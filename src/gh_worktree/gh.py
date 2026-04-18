import json
import subprocess

from gh_worktree.context import Context


class GithubCLI:
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

    def pr_status(self, pr_number: int | str, owner_repo: str | None = None):
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
        args = ["pr", "view", "--json"]
        if owner_repo:
            args.extend(["--repo", owner_repo])
        args.extend([",".join(fields), pr_number])
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

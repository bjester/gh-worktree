import json

from gh_worktree.subprocess import SubprocessOperator

PR_FIELDS = [
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
REPO_FIELDS = [
    "defaultBranchRef",
    "name",
    "owner",
    "url",
    "isPrivate",
]


class GithubCLI(SubprocessOperator):
    command_name = "gh"

    def pr_status(self, pr_number: int | str, owner_repo: str | None = None) -> dict:
        args = ["pr", "view"]
        if owner_repo:
            args.extend(["--repo", owner_repo])
        args.extend(["--json", ",".join(PR_FIELDS), str(pr_number)])
        with self.run(args) as p:
            output = p.stdout
        return json.loads(output)

    def repo_status(self) -> dict:
        with self.run(["repo", "view", "--json", ",".join(REPO_FIELDS)]) as p:
            output = p.stdout
        return json.loads(output)

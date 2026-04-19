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

    def pr_status(self, pr_number: int | str, owner_repo: str | None = None):
        args = ["pr", "view"]
        if owner_repo:
            args.extend(["--repo", owner_repo])
        args.extend(["--json", ",".join(PR_FIELDS), str(pr_number)])
        output = self.run(args).stdout
        return json.loads(output)

    def repo_status(self):
        output = self.run(["repo", "view", "--json", ",".join(REPO_FIELDS)]).stdout
        return json.loads(output)

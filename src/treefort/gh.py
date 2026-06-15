import json

from treefort.subprocess import SubprocessOperator

PR_FIELDS = [
    "number",
    "author",
    "baseRefName",
    "headRefName",
    "headRefOid",
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

    def merged_pr_by_head(self, head_ref_name: str, owner_repo: str | None = None) -> list[dict]:
        """Get merged PR info for a given head ref name"""
        args = [
            "pr",
            "list",
            "--head",
            head_ref_name,
            "--state",
            "merged",
            "--json",
            ",".join(PR_FIELDS),
        ]
        if owner_repo:
            args.extend(["--repo", owner_repo])
        try:
            with self.run(args) as p:
                output = p.stdout
            prs = json.loads(output)
            if prs:
                return prs
        except Exception:
            pass
        return []

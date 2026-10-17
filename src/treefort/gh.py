import json
import subprocess

from treefort.errors import CommandError
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


def _error_detail(error: subprocess.CalledProcessError) -> str:
    """
    Returns the most useful diagnostic text available from a failed command.

    GitHub CLI errors are written to standard error, so it takes precedence. `subprocess.run`
    stores standard output on the `output` attribute rather than `stdout`, so both are checked
    before falling back to the generic exception text.

    :param error: The captured subprocess exception.
    :return: Diagnostic text to include in the translated error.
    :rtype: str
    """
    stderr = (getattr(error, "stderr", None) or "").strip()
    stdout = (getattr(error, "output", None) or getattr(error, "stdout", None) or "").strip()
    return stderr or stdout or str(error)


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
        """
        Get merged PR info for a given head ref name

        A failed lookup raises instead of returning an empty list, so callers cannot mistake an
        authentication, repository, or decoding failure for a query that found no merged PRs.

        :param head_ref_name: The branch name whose merged pull requests are requested.
        :type head_ref_name: str
        :param owner_repo: The ``owner/name`` repository to query. When omitted, ``gh`` infers the
            repository from the current Git context.
        :type owner_repo: str | None
        :return: The matching merged pull requests. An empty list means the query succeeded and
            found nothing.
        :rtype: list[dict]
        :raises CommandError: If the GitHub CLI exits with a nonzero status or its response cannot
            be decoded as a JSON list of pull request objects.
        """
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
        except subprocess.CalledProcessError as e:
            raise CommandError(
                f"Failed to query merged PRs for branch '{head_ref_name}': {_error_detail(e)}"
            ) from e

        try:
            prs = json.loads(output)
        except json.JSONDecodeError as e:
            raise CommandError(
                f"Invalid JSON response for merged PR query on branch '{head_ref_name}': {e}"
            ) from e

        if not isinstance(prs, list) or not all(isinstance(pr, dict) for pr in prs):
            raise CommandError(
                f"Invalid response for merged PR query on branch '{head_ref_name}': "
                "expected a list of PR objects"
            )
        return prs

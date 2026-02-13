# gh-worktree

A CLI tool that helps you manage Git worktrees. This was built as a GitHub CLI (`gh`) extension, but it can be used directly. Although it does rely on the following being available:
- `git` (obviously)
- `gh`

When you use `gh-worktree` to initialize a repository for use with worktrees, it uses a bare repository approach, which creates a structure like the following, if you were to clone `gh-worktree`:
```
gh-worktree/
  .bare/
  .git # points git to .bare/
  .gh/
    worktree/
      hooks/
      config.json
```
When you create new worktrees, they'll be added as directories to the root directory:
```
gh-worktree/
  # ... see above ...
  my-new-worktree/
    README.md
    # ... etc ...
```

You may add hooks to `.gh/worktree/hooks` so that you may trigger custom functionality during the lifecycle of your worktrees. The hooks are configurable in the project, but also globally. The first global `.gh/worktree/hooks` found upwards in the directory tree, outside the project directory (i.e. above `gh-worktree/`), will be executed. The following hooks are available:
- `pre_init`: before initializing a repository for use with worktrees (global only)
- `post_init`: after initializing a repository for use with worktrees (global only)
- `pre_checkout`: before a PR or other existing branch is checked out as a worktree
- `post_checkout`: after a PR or other existing branch is checked out as a worktree
- `pre_create`: before a new worktree (branch) is created
- `post_create`: after a new worktree (branch) is created
- `pre_remove`: before a worktree is removed
- `post_remove`: after a worktree is removed

For example, you might consider adding a `post_create` hook for this project like:
```bash
#!/usr/bin/env bash

WORKTREE_NAME="$1"
BASE_REF="$2" # format: `remote/branch`

pushd "$WORKTREE_NAME"

uv venv
uv sync --group dev

popd
```

## Commands
You may use `--help` for any command for usage information. To see a list of commands, run `gh-worktree` without any arguments.

### Init
**Spec: `init <repository_uri> [optional_clone_dir]`**

Initializes the repository (e.g. `https://github.com/bjester/gh-worktree.git`) for use with this plugin and git worktrees. It's similar to `git clone` in that you can specify a name for the project directory as the second argument, otherwise it uses the repository name.

### Create
**Spec: `create <worktree_name> [base_ref]`**

Creates a new worktree, which by default will be based off the default branch of the Github repository that you initialized the project with using `init`.

### Checkout
**Spec: `checkout [--remote=<name>] <branch_name|pr_number|pr_url>`**

Similar to how `gh` lets you quickly checkout PRs, this command allows you to quickly create a worktree for a PR. This works even if the PR was opened from a fork of the project, and regardless of whether you've configured the fork as a remote.

### Remove
**Spec: `remove [--force] <worktree_name>`**

Removes a worktree. If git detects the worktree has commits that are unmerged, then it will refuse to delete it. You may use `--force` to passthrough `--force` to git and force the worktree's deletion.

## Installation as `gh` extension
TBD

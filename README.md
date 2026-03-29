# gh-worktree

[![Python tests](https://github.com/bjester/gh-worktree/actions/workflows/pytest.yml/badge.svg?branch=main)](https://github.com/bjester/gh-worktree/actions/workflows/pytest.yml)
[![Build](https://github.com/bjester/gh-worktree/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/bjester/gh-worktree/actions/workflows/build.yml)
[![PyPI](https://img.shields.io/pypi/v/gh-worktree.svg?color=blue)](https://pypi.org/project/gh-worktree/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org)

A CLI tool that helps you manage Git worktrees. Built as a GitHub CLI (`gh`) extension, but works standalone.

**Dependencies:** `git`, [`gh`](https://cli.github.com/)

---

## Table of Contents

- [Quick Start](#quick-start)
- [Capabilities](#capabilities)
- [How It Works](#how-it-works)
  - [Directory Structure](#directory-structure)
  - [Hooks](#hooks)
  - [Templates](#templates)
- [Commands](#commands)
  - [init](#commands-init)
  - [create](#commands-create)
  - [checkout](#commands-checkout)
  - [remove](#commands-remove)
  - [install](#commands-install)
  - [version](#commands-version)
- [Installation](#installation)
- [AI Disclosure](#ai-disclosure)
- [License](#license)

---

## Quick Start

```bash
pip install gh-worktree
```

Or with uv:

```bash
uvx gh-worktree
```

Or download the PEX file from the [releases page](https://github.com/bjester/gh-worktree/releases).

See [recipes](https://github.com/bjester/gh-worktree-recipes) for hooks and templates.

---

## Capabilities

| Feature | Description |
|---------|-------------|
| **Bare repository initialization** | Clean separation of git metadata from worktrees |
| **Lifecycle hooks** | Custom scripts at key points with checksum validation |
| **Global + project config** | Hooks and templates at both levels |
| **PR worktrees** | Create worktrees directly from GitHub PRs |
| **Project bootstrapping** | Auto-copy hooks/templates from repo on init |
| **Worktree templates** | Pre-configured files copied to new worktrees |
| **Environment variables** | Template variables with allowlist support |

---

## How It Works

### Directory Structure

After initializing a repository (e.g., `gh-worktree`):

```
gh-worktree/
  .bare/                 # Bare git repository
  .git                   # Points to .bare/
  .gh/
    worktree/
      hooks/             # Project-level hooks
      templates/         # Project-level templates
      config.json        # Project configuration
  my-new-worktree/       # Created worktrees
    README.md
    ...
```

### Hooks

Hooks are executable scripts that run at specific lifecycle points. They can be configured at:
- **Global level**: `~/.gh/worktree/hooks/` (or parent directories outside the project)
- **Project level**: `.gh/worktree/hooks/` (copied from repo on init if present)

Execution order: global hooks first, then project hooks.

| Hook | Executes At | Description |
|------|-------------|-------------|
| `pre_init` | Global only | Before initializing a repository for worktrees |
| `post_init` | Global + Project | After initializing a repository for worktrees |
| `pre_checkout` | Global + Project | Before checking out a PR or existing branch as a worktree |
| `post_checkout` | Global + Project | After checking out a PR or existing branch as a worktree |
| `pre_create` | Global + Project | Before creating a new worktree (branch) |
| `post_create` | Global + Project | After creating a new worktree (branch) |
| `pre_remove` | Global + Project | Before removing a worktree |
| `post_remove` | Global + Project | After removing a worktree |

Hooks must be executable and allowed (via checksum validation) to run.

<details>
<summary><strong>Example: post_create hook</strong></summary>

A hook for this project might look something like:

```bash
#!/usr/bin/env bash

WORKTREE_NAME="$1"            # Full worktree name
BASE_REF="$2"                 # Format: remote/branch
WORKTREE_NAME_NORMALIZED="$3" # Worktree name with non-alphanumeric characters replaced by dashes

pushd "$WORKTREE_NAME"

uv venv
uv sync --group dev
prek install -f

popd
```

</details>

### Templates

Files in `.gh/worktree/templates/` are copied to new worktrees before post-hooks execute.

**Tip:** Add template files to `.gitignore`.

Templates support environment variable substitution using `${ENVVAR_NAME}` syntax. Allowlist variable names in `~/.gh/worktree/config.json` under `allowed_envvars`.

**Provided variables:**

| Variable | Description |
|----------|-------------|
| `REPO_NAME` | Name of the git repository |
| `REPO_DIR` | Absolute path of the repo / project directory |
| `WORKTREE_NAME` | Name of the new worktree |
| `WORKTREE_NAME_NORMALIZED` | Worktree name with non-alphanumeric chars replaced by dashes |
| `WORKTREE_DIR` | Absolute path of the worktree directory |

<details>
<summary><strong>Example: JetBrains project name template</strong></summary>

Set a unique project name per worktree in JetBrains IDEs:

**File:** `.gh/worktree/templates/.idea/.name`

```
${REPO_NAME}.${WORKTREE_NAME_NORMALIZED}
```

**Result in worktree:** `.idea/.name` contains `gh-worktree.feat-my-branch`

</details>

---

## Commands

Run `gh-worktree` without any arguments for usage information.

<details>
<summary><strong><a id="commands-init">init</a></strong> — Initialize a repository for worktrees</summary>

**Spec:** `init <repository_uri> [optional_clone_dir] [--yes]`

Initializes a repository for use with worktrees. Similar to `git clone` — specify a directory name as the second argument, or it defaults to the repository name.

- `--yes`: Automatically execute new or modified hooks without prompting

</details>

<details>
<summary><strong><a id="commands-create">create</a></strong> — Create a new worktree</summary>

**Spec:** `create <worktree_name> [base_ref] [--yes]`

Creates a new worktree. Defaults to the default branch of the GitHub repository. Optionally specify a base reference.

- `--yes`: Automatically execute new or modified hooks without prompting

</details>

<details>
<summary><strong><a id="commands-checkout">checkout</a></strong> — Checkout a PR or branch as a worktree</summary>

**Spec:** `checkout [--remote=<name>] [--yes] <branch_name|pr_number|pr_url>`

Quickly create a worktree for a PR or existing branch. Works with fork PRs regardless of remote configuration.

- `--yes`: Automatically execute new or modified hooks without prompting

</details>

<details>
<summary><strong><a id="commands-remove">remove</a></strong> — Remove a worktree</summary>

**Spec:** `remove [--force] [--yes] <worktree_name>`

**Aliases:** `rm`

Removes a worktree. Git refuses to delete worktrees with unmerged commits unless `--force` is used.

- `--yes`: Automatically execute new or modified hooks without prompting

</details>

<details>
<summary><strong><a id="commands-install">install</a></strong> — Install gh-worktree</summary>

**Spec:** `install [--alias=<name>] [--gh-ext] [--path-bin] [--force]`

Installs gh-worktree as a GitHub CLI extension or to your PATH. Without options, prompts for installation method.

- `--gh-ext`: Install as `gh` extension
- `--path-bin`: Install to `~/.local/bin` or `~/bin`
- `--alias`: Custom name (e.g., `wktr`)
- `--force`: Overwrite existing installation

</details>

<details>
<summary><strong><a id="commands-version">version</a></strong> — Show version</summary>

**Spec:** `version`

Outputs the installed version of gh-worktree.

</details>

---

## Installation

Tested on Linux. Requires Python 3.10+ for PEX.

### As a GitHub CLI extension (`gh`)

1. Download the [latest release](https://github.com/bjester/gh-worktree/releases) binary.
2. Make executable: `chmod +x gh-worktree`
3. Install: `./gh-worktree install --gh-ext`
4. Test: `gh worktree`

### Standalone

1. Download the [latest release](https://github.com/bjester/gh-worktree/releases) binary or PEX.
2. Make executable: `chmod +x gh-worktree*`
3. Install: `./gh-worktree install --path-bin` or `./gh-worktree.pex install --path-bin`
4. Test: `gh-worktree version`

### Aliasing

```bash
./gh-worktree install --alias=wktr --path-bin
wktr version
```

### From source

```bash
git clone https://github.com/bjester/gh-worktree.git
cd gh-worktree
uv venv
source .venv/bin/activate
uv sync --group dev
make dist/gh-worktree
./dist/gh-worktree install --path-bin
```

---

## AI Disclosure

LLMs were used in the development of this project, mostly for brainstorming and bootstrapping code, particularly tests. The contribution proportion is roughly 80 / 20, human and AI code respectively. This may change over time as I try out agents!

---

## License

[MIT](LICENSE) :: Copyright 2026 Blaine Jester

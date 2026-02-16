# AGENTS instructions

## Introduction

This document governs the project `gh-worktree`. The project is a CLI utility that assists software developers in their use of git worktrees. The project uses `python-fire` to provide the CLI and is structured into classes which represent the commands that can be invoked.

## Structure
- The source code is located in `src/gh_worktree/`
- The primary CLI command class is located in `src/gh_worktree/main.py`
- The sub-command classes are located in `src/gh_worktree/commands/`
- The tests are located in `tests/`

## Development environment

### Tooling
* Package management: uv - installs and manages python dependencies, and builds the project.
* Code formatter: black - Enforces consistent formatting automatically.
* Linter: flake8 - Identifies potential issues and style violations.
* Pre-commit: pre-commit - executes formatter and linter, and other checks prior to commit.

### Details
- Use `uv venv` to create a virtual environment into `.venv/` which can otherwise be ignored.
- Use `uv sync --dev` to install python packages.
- Use `uv run pytest` to run the test suite.
- Use `make build` to build the project, generating `.whl` and `.pex` files in `dist/`.
- The `gh-worktree` command can be tested within the `playground/` directory
- Find CI plans in the .github/workflows folder.

## Style Guide
- See `.gemini/styleguide.md` for overall style guidance
- See `.aiassistant/rules/tests.md` for unit test styles

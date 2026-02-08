SHELL := /bin/bash

.PHONY: build

build:
	rm -rf ./dist
	uv build --wheel --out-dir ./dist
	uv tool run pex==2.88.1 -v . -e gh_worktree.cli:main -o dist/gh-worktree.pex
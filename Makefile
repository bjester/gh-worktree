SHELL := /bin/bash

.PHONY: build build-whl clean install

build: | clean
	$(MAKE) build-whl
	$(MAKE) dist/gh-worktree.pex
	$(MAKE) dist/gh-worktree

dist/gh-worktree:
	uv run pyinstaller gh-worktree.spec

dist/gh-worktree.pex:
	uv tool run pex==2.88.1 -v . -e gh_worktree.cli:main -o dist/gh-worktree.pex

build-whl:
	uv build --wheel --out-dir ./dist

clean:
	rm -rf ./build ./dist

install: | dist/gh-worktree
	./dist/gh-worktree install

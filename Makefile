SHELL := /bin/bash

.PHONY: build build-whl clean install

build: | clean
	$(MAKE) build-whl
	$(MAKE) dist/treefort.pex
	$(MAKE) dist/treefort

dist/treefort:
	uv run pyinstaller treefort.spec

dist/treefort.pex:
	uv run pex -v . -e treefort.cli:main -o dist/treefort.pex

build-whl:
	uv build --wheel --out-dir ./dist

clean:
	rm -rf ./build ./dist

install: | dist/treefort
	./dist/treefort install

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gh-worktree")
except PackageNotFoundError:
    # Package is not installed
    __version__ = "unknown"

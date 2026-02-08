from typing import List

from gh_worktree.context import Context
from gh_worktree.runtime import Runtime


class BaseCommand(object):
    def __init__(self):
        pass


class Command(BaseCommand):
    _name: str
    _aliases: List[str] = []

    def __init__(self, runtime: Runtime):
        super().__init__()
        self._runtime = runtime

    @property
    def _context(self) -> Context:
        return self._runtime.context

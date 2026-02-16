import json
from typing import Dict
from typing import List


class Config(object):
    type: str

    def __init__(self):
        self._data = {"type": getattr(self, "type", "unknown")}

    def update(self, **kwargs):
        self._data.update(kwargs)

    def save(self, fd):
        json.dump(self._data, fd, indent=4)

    @classmethod
    def load(cls, fd):
        config = cls()
        config_data = json.load(fd)
        if config_data["type"] != cls.type:
            raise ValueError(f"Invalid config type: {config_data['type']}")
        config._data = config_data
        return config


class GlobalConfig(Config):
    type: str = "global"

    @property
    def allowed_hooks(self) -> Dict[str, str]:
        return self._data.get("allowed_hooks", {})

    @property
    def allowed_envvars(self) -> List[str]:
        return self._data.get("allowed_envvars", [])

    def allow_hook(self, path: str, checksum: str):
        hooks = self.allowed_hooks.copy()
        hooks[path] = checksum
        self._data["allowed_hooks"] = hooks


class RepositoryConfig(Config):
    type: str = "repository"

    @property
    def default_branch(self) -> str:
        return self._data.get("default_branch", "main")

    @property
    def owner(self) -> str:
        return self._data.get("owner")

    @property
    def name(self) -> str:
        return self._data.get("name")

    @property
    def url(self) -> str:
        return self._data.get("url")

    @property
    def is_private(self) -> bool:
        return self._data.get("is_private", False)

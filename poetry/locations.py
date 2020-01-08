from pathlib import Path
from typing import Dict

from .utils.appdirs import user_cache_dir
from .utils.appdirs import user_config_dir


class Locations(object):
    def __init__(self, env_vars):  # type: (Dict[str, str]) -> None
        self._cache_dir = user_cache_dir("pypoetry", env_vars)
        self._config_dir = user_config_dir("pypoetry", env_vars)

    @property
    def cache_dir(self):  # type: () -> Path
        return Path(self._cache_dir)

    @property
    def config_dir(self):  # type: () -> Path
        return Path(self._config_dir)

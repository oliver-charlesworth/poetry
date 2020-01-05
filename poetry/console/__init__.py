import os

from pathlib import Path
from typing import Dict

from ..factory import Factory
from .application import Application
from ..poetry import Poetry


def main():
    def _create_poetry(env_vars, cwd):  # type: (Dict[str, str], Path) -> Poetry
        return Factory(env_vars=env_vars, cwd=cwd).create_poetry()

    return Application(
        env_vars=os.environ, cwd=Path.cwd(), create_poetry=_create_poetry
    ).run()

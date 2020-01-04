import os
from pathlib import Path

from .application import Application
from ..factory import Factory


def main():
    return Application(
        env_vars=os.environ,
        cwd=Path.cwd(),
        create_poetry=Factory().create_poetry
    ).run()

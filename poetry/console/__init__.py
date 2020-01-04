import os

from pathlib import Path

from ..factory import Factory
from .application import Application


def main():
    return Application(
        env_vars=os.environ, cwd=Path.cwd(), create_poetry=Factory().create_poetry
    ).run()

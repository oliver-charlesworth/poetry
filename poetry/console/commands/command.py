from pathlib import Path
from typing import Dict

from cleo import Command as BaseCommand

from poetry.poetry import Poetry


class Command(BaseCommand):

    loggers = []

    @property
    def poetry(self):  # type: () -> Poetry
        return self.application.poetry

    @property
    def env_vars(self):  # type: () -> Dict[str, str]
        return self.application.env_vars

    @property
    def cwd(self):  # type: () -> Path
        return self.application.cwd

    def reset_poetry(self):  # type: () -> None
        self.application.reset_poetry()

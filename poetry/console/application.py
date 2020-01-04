from pathlib import Path
from typing import Callable
from typing import Dict

from cleo import Application as BaseApplication

from poetry import __version__

from ..poetry import Poetry
from .commands.about import AboutCommand
from .commands.add import AddCommand
from .commands.build import BuildCommand
from .commands.cache.cache import CacheCommand
from .commands.check import CheckCommand
from .commands.config import ConfigCommand
from .commands.debug.debug import DebugCommand
from .commands.env.env import EnvCommand
from .commands.export import ExportCommand
from .commands.init import InitCommand
from .commands.install import InstallCommand
from .commands.lock import LockCommand
from .commands.new import NewCommand
from .commands.publish import PublishCommand
from .commands.remove import RemoveCommand
from .commands.run import RunCommand
from .commands.search import SearchCommand
from .commands.self.self import SelfCommand
from .commands.shell import ShellCommand
from .commands.show import ShowCommand
from .commands.update import UpdateCommand
from .commands.version import VersionCommand
from .config import ApplicationConfig


class Application(BaseApplication):
    def __init__(
        self,
        env_vars,  # type: Dict[str, str]
        cwd,  # type: Path
        create_poetry,  # type: Callable[[Dict[str, str], Path], Poetry]
    ):  # type: (...) -> None
        super(Application, self).__init__(
            "poetry", __version__, config=ApplicationConfig("poetry", __version__)
        )

        self._poetry = None
        self._create_poetry = create_poetry
        self._env_vars = env_vars
        self._cwd = cwd

        for command in self.get_default_commands():
            self.add(command)

    @property
    def env_vars(self):  # type: () -> Dict[str, str]
        return self._env_vars  # TODO - should we return a copy?

    @property
    def cwd(self):  # type: () -> Path
        return self._cwd

    @property
    def poetry(self):
        if self._poetry is None:
            self._poetry = self._create_poetry(self._env_vars, self._cwd)

        return self._poetry

    def reset_poetry(self):  # type: () -> None
        self._poetry = None

    def get_default_commands(self):  # type: () -> list
        commands = [
            AboutCommand(),
            AddCommand(),
            BuildCommand(),
            CheckCommand(),
            ConfigCommand(),
            ExportCommand(),
            InitCommand(),
            InstallCommand(),
            LockCommand(),
            NewCommand(),
            PublishCommand(),
            RemoveCommand(),
            RunCommand(),
            SearchCommand(),
            ShellCommand(),
            ShowCommand(),
            UpdateCommand(),
            VersionCommand(),
        ]

        # Cache commands
        commands += [CacheCommand()]

        # Debug command
        commands += [DebugCommand()]

        # Env command
        commands += [EnvCommand()]

        # Self commands
        commands += [SelfCommand()]

        return commands

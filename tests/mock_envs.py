import os
import sys

from pathlib import Path
from typing import Tuple

from poetry.semver import Version
from poetry.utils.env import SystemEnv
from tests.conftest import minimal_env_vars


class NullEnv(SystemEnv):
    def __init__(self, path=None, base=None, execute=False):
        if path is None:
            path = Path(sys.prefix)

        super(NullEnv, self).__init__(path, base=base)

        self._execute = execute
        self.executed = []

    def _run(self, cmd, env_vars, cwd, input):
        self.executed.append(cmd)

        if self._execute:
            return super(NullEnv, self)._run(cmd, env_vars, cwd, input)

    def execute(self, cmd, env_vars, cwd):
        self.executed.append(cmd)

        if self._execute:
            return super(NullEnv, self).execute(cmd=cmd, env_vars=env_vars, cwd=cwd)

    def _bin(self, bin):
        return bin


class MockEnv(NullEnv):
    def __init__(
        self,
        version_info=(3, 7, 0),
        python_implementation="CPython",
        platform="darwin",
        os_name="posix",
        is_venv=False,
        pip_version="19.1",
        **kwargs
    ):
        super(MockEnv, self).__init__(**kwargs)

        self._version_info = version_info
        self._python_implementation = python_implementation
        self._platform = platform
        self._os_name = os_name
        self._is_venv = is_venv
        self._pip_version = Version.parse(pip_version)

    @property
    def version_info(self):  # type: () -> Tuple[int]
        return self._version_info

    @property
    def python_implementation(self):  # type: () -> str
        return self._python_implementation

    @property
    def platform(self):  # type: () -> str
        return self._platform

    @property
    def os(self):  # type: () -> str
        return self._os_name

    @property
    def pip_version(self):
        return self._pip_version

    def is_venv(self):  # type: () -> bool
        return self._is_venv

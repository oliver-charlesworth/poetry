import base64
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import sysconfig
import warnings

from contextlib import contextmanager
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import tomlkit

from clikit.api.io import IO

from poetry.locations import CACHE_DIR
from poetry.poetry import Poetry
from poetry.semver import parse_constraint, VersionConstraint
from poetry.semver.version import Version
from poetry.utils._compat import CalledProcessError
from poetry.utils._compat import Path
from poetry.utils._compat import decode
from poetry.utils._compat import encode
from poetry.utils._compat import list_to_shell_command
from poetry.utils._compat import subprocess
from poetry.utils.toml_file import TomlFile
from poetry.version.markers import BaseMarker


GET_ENVIRONMENT_INFO = """\
import json
import os
import platform
import sys

if hasattr(sys, "implementation"):
    info = sys.implementation.version
    iver = "{0.major}.{0.minor}.{0.micro}".format(info)
    kind = info.releaselevel
    if kind != "final":
        iver += kind[0] + str(info.serial)

    implementation_name = sys.implementation.name
else:
    iver = "0"
    implementation_name = ""

env = {
    "implementation_name": implementation_name,
    "implementation_version": iver,
    "os_name": os.name,
    "platform_machine": platform.machine(),
    "platform_release": platform.release(),
    "platform_system": platform.system(),
    "platform_version": platform.version(),
    "python_full_version": platform.python_version(),
    "platform_python_implementation": platform.python_implementation(),
    "python_version": platform.python_version()[:3],
    "sys_platform": sys.platform,
    "version_info": tuple(sys.version_info),
}

print(json.dumps(env))
"""


GET_BASE_PREFIX = """\
import sys

if hasattr(sys, "real_prefix"):
    print(sys.real_prefix)
elif hasattr(sys, "base_prefix"):
    print(sys.base_prefix)
else:
    print(sys.prefix)
"""

GET_CONFIG_VAR = """\
import sysconfig

print(sysconfig.get_config_var("{config_var}")),
"""

GET_PYTHON_VERSION = """\
import sys

print('.'.join([str(s) for s in sys.version_info[:3]]))
"""

GET_SYS_PATH = """\
import json
import sys

print(json.dumps(sys.path))
"""

CREATE_VENV_COMMAND = """\
path = {!r}

try:
    from venv import EnvBuilder

    builder = EnvBuilder(with_pip=True)
    build = builder.create
except ImportError:
    # We fallback on virtualenv for Python 2.7
    from virtualenv import create_environment

    build = create_environment

build(path)"""


class EnvError(Exception):

    pass


class EnvCommandError(EnvError):
    def __init__(self, e, input=None):  # type: (CalledProcessError) -> None
        self.e = e

        message = "Command {} errored with the following return code {}, and output: \n{}".format(
            e.cmd, e.returncode, decode(e.output)
        )
        if input:
            message += "input was : {}".format(input)
        super(EnvCommandError, self).__init__(message)


class NoCompatiblePythonVersionFound(EnvError):
    def __init__(self, expected, given=None):
        if given:
            message = (
                "The specified Python version ({}) "
                "is not supported by the project ({}).\n"
                "Please choose a compatible version "
                "or loosen the python constraint specified "
                "in the pyproject.toml file.".format(given, expected)
            )
        else:
            message = (
                "Poetry was unable to find a compatible version. "
                "If you have one, you can explicitly use it "
                'via the "env use" command.'
            )

        super(NoCompatiblePythonVersionFound, self).__init__(message)


class EnvManager(object):
    """
    Environments manager
    """

    _env = None

    ENVS_FILE = "envs.toml"

    def __init__(self, poetry):  # type: (Poetry) -> None
        self._poetry = poetry

    def activate(self, executable_or_version, io):  # type: (str, IO) -> Env
        python_exec = self._exec_or_version_to_exec(executable_or_version)

        if self._root_venv:
            self._activate_root(python_exec, io)
        else:
            self._activate_non_root(python_exec, io)

        return self.get()

    def _activate_root(self, python_exec, io):  # type: (str, IO) -> None
        version = self._python_version(python_exec)
        recreate = self._root_venv_path.exists() and version != self._version_from_info(VirtualEnv(self._root_venv_path).version_info)
        self.create_venv(io, executable=python_exec, force_recreate=recreate)

    def _activate_non_root(self, python_exec, io):  # type: (str, IO) -> Env
        version = self._python_version(python_exec)
        active_version = self._read_active_version()
        recreate = active_version and self._same_minor(active_version, version) and not self._same_patch(active_version, version)
        if not self._venv_path(version).exists() or recreate:
            self.create_venv(io, executable=python_exec, force_recreate=True)

        self._write_active_version(version)

    def deactivate(self, io):  # type: (IO) -> None
        active_version = self._read_active_version()
        if active_version:
            io.write_line(
                "Deactivating virtualenv: <comment>{}</comment>".format(self._venv_path(active_version))
            )
            self._delete_active_version()

    def get(self):  # type: () -> Env
        active_version = self._read_active_version()

        # Conda sets CONDA_PREFIX in its envs, see https://github.com/conda/conda/issues/2764.
        env_prefix = os.environ.get("VIRTUAL_ENV", os.environ.get("CONDA_PREFIX"))
        # We manage an existing virtualenv or Conda env if we're already running in it.
        # Though we don't pollute Conda's global "base" env, and we give an explicitly activated
        # Poetry venv priority.
        use_external_venv = (
            not active_version
            and env_prefix is not None
            and os.environ.get("CONDA_DEFAULT_ENV") != "base"
        )

        if use_external_venv:
            return VirtualEnv(Path(env_prefix))

        # TODO - this should be based on whether self._root_venv is true, no?
        venv_path = self._root_venv_path
        if venv_path.exists() and venv_path.is_dir():
            return VirtualEnv(venv_path)

        venv_path = self._venv_path(active_version or self._version_from_info())
        if self._create_venv and venv_path.exists():
            return VirtualEnv(venv_path)

        return SystemEnv(Path(sys.prefix))

    def list(self):  # type: () -> List[VirtualEnv]
        venv_name = self.generate_env_name()
        venvs_path = self._venvs_path

        return [
            VirtualEnv(Path(p))
            for p in sorted(venvs_path.glob("{}-py*".format(venv_name)))
        ]

    def remove(self, env_name_or_executable_or_version):  # type: (str) -> Env
        if env_name_or_executable_or_version.startswith(self.generate_env_name()):
            venv, version = self._find_venv_by_name(env_name_or_executable_or_version)
        else:
            venv, version = self._find_venv_by_executable_or_version(env_name_or_executable_or_version)

        active_version = self._read_active_version()
        if active_version and self._same_minor(active_version, version):
            self._delete_active_version()

        self.remove_venv(str(venv.path))
        return venv

    def _find_venv_by_name(self, env_name):  # type: (str) -> (Env, Version)
        for venv in self.list():
            if venv.path.name == env_name:
                return venv, self._version_from_info(venv.version_info)

        raise ValueError(
            '<warning>Environment "{}" does not exist.</warning>'.format(env_name)
        )

    def _find_venv_by_executable_or_version(self, executable_or_version):  # type: (str) -> (Env, Version)
        executable = self._exec_or_version_to_exec(executable_or_version)
        version = self._python_version(executable)
        venv_path = self._venv_path(version)

        if not venv_path.exists():
            raise ValueError(
                '<warning>Environment "{}" does not exist.</warning>'.format(venv_path.name)
            )

        return VirtualEnv(venv_path), version

    def create_venv(
        self, io, executable=None, force_recreate=False
    ):  # type: (IO, Optional[str], bool) -> Env
        if self._env is not None and not force_recreate:
            return self._env

        env = self.get()
        if env.is_venv() and not force_recreate:
            # Already inside a virtualenv.
            return env

        executable, version = self._select_python_executable(io, executable)

        if self._root_venv:
            venv_path = self._root_venv_path
        else:
            venv_path = self._venv_path(version)

        if not venv_path.exists():
            if not self._create_venv:
                io.write_line(
                    "<fg=black;bg=yellow>"
                    "Skipping virtualenv creation, "
                    "as specified in config file."
                    "</>"
                )

                return SystemEnv(Path(sys.prefix))

            io.write_line(
                "Creating virtualenv <c1>{}</> in {}".format(venv_path.name, str(venv_path))
            )

            self.build_venv(str(venv_path), executable=executable)
        else:
            if force_recreate:
                io.write_line(
                    "Recreating virtualenv <c1>{}</> in {}".format(venv_path.name, str(venv_path))
                )
                self.remove_venv(str(venv_path))
                self.build_venv(str(venv_path), executable=executable)
            elif io.is_very_verbose():
                io.write_line("Virtualenv <c1>{}</> already exists.".format(venv_path.name))

        return self.get()

    def _select_python_executable(self, io, executable):  # type (IO, Optional[str]) -> (Optional[str], Version)
        constraint = self._poetry.package.python_constraint
        if executable:
            version = self._python_version(executable)

            if not constraint.allows(version):
                raise NoCompatiblePythonVersionFound(
                    self._poetry.package.python_versions, version
                )
        else:
            version = self._version_from_info()

            if not constraint.allows(version):
                io.write_line(
                    "<warning>The currently activated Python version {} "
                    "is not supported by the project ({}).\n"
                    "Trying to find and use a compatible version.</warning> ".format(
                        version, self._poetry.package.python_versions
                    )
                )

                executable, version = self._find_compatible_python(io, constraint)

                if not executable:
                    raise NoCompatiblePythonVersionFound(
                        self._poetry.package.python_versions
                    )

        return executable, version

    def _find_compatible_python(self, io, constraint):  # type: (IO, VersionConstraint) -> (str, Version)
        for python_to_try in reversed(
                sorted(
                    self._poetry.package.AVAILABLE_PYTHONS,
                    key=lambda v: (v.startswith("3"), -len(v), v),
                )
        ):
            if len(python_to_try) == 1:
                if not parse_constraint("^{}.0".format(python_to_try)).allows_any(constraint):
                    continue
            elif not constraint.allows_all(parse_constraint(python_to_try + ".*")):
                continue

            executable = "python" + python_to_try

            if io.is_debug():
                io.write_line("<debug>Trying {}</debug>".format(executable))

            try:
                version = self._python_version(executable)
            except EnvCommandError:
                continue

            if constraint.allows(version):
                io.write_line("Using <c1>{}</c1> ({})".format(executable, version))
                return executable, version

        return None, None

    @classmethod
    def build_venv(cls, path, executable=None):
        if executable is not None:
            # Create virtualenv by using an external executable
            try:
                p = subprocess.Popen(
                    list_to_shell_command([executable, "-"]),
                    stdin=subprocess.PIPE,
                    shell=True,
                )
                p.communicate(encode(CREATE_VENV_COMMAND.format(path)))
            except CalledProcessError as e:
                raise EnvCommandError(e)

            return

        try:
            from venv import EnvBuilder

            # use the same defaults as python -m venv
            builder = EnvBuilder(with_pip=True, symlinks=(os.name != "nt"))
            build = builder.create
        except ImportError:
            # We fallback on virtualenv for Python 2.7
            from virtualenv import create_environment

            build = create_environment

        build(path)

    def remove_venv(self, path):  # type: (str) -> None
        shutil.rmtree(path)

    def get_base_prefix(self):  # type: () -> Path
        if hasattr(sys, "real_prefix"):
            return sys.real_prefix

        if hasattr(sys, "base_prefix"):
            return sys.base_prefix

        return sys.prefix

    def _venv_path(self, version):  # type: (Version) -> Path
        name = "{}-py{}.{}".format(self.generate_env_name(), version.major, version.minor)
        return self._venvs_path / name

    # TODO - should cache this, as we call it a lot?
    def generate_env_name(self):  # type: () -> str
        sanitized_name = re.sub(r'[ $`!*@"\\\r\n\t]', "_", self._poetry.package.name.lower())[:42]
        h = hashlib.sha256(encode(str(self._poetry.file.parent))).digest()
        h = base64.urlsafe_b64encode(h).decode()[:8]

        return "{}-{}".format(sanitized_name, h)

    def _read_envs_file(self):
        if self._envs_file.exists():
            return self._envs_file.read()
        else:
            return tomlkit.document()

    def _read_active_version(self):  # type: () -> Optional[Version]
        name = self.generate_env_name()
        records = self._read_envs_file()
        record = records.get(name)
        if record:
            return Version.parse(record["patch"])
        else:
            return None

    def _write_active_version(self, version):  # type: (Version) -> None
        name = self.generate_env_name()
        records = self._read_envs_file()
        records[name] = {
            "minor": "{}.{}".format(version.major, version.minor),  # TODO - can we eliminate this?
            "patch": "{}.{}.{}".format(version.major, version.minor, version.patch)
        }
        self._envs_file.write(records)

    def _delete_active_version(self):
        name = self.generate_env_name()
        records = self._read_envs_file()
        if name in records:
            del records[name]
        self._envs_file.write(records)

    @classmethod
    def _python_version(cls, executable):  # type: (str) -> Version
        try:
            return Version.parse(decode(
                subprocess.check_output(
                    list_to_shell_command(
                        [
                            executable,
                            "-c",
                            GET_PYTHON_VERSION,
                        ]
                    ),
                    shell=True,
                )
            ).strip())
        except CalledProcessError as e:
            raise EnvCommandError(e)

    @classmethod
    def _version_from_info(cls, info=None):  # type: (Optional[Tuple[int]]) -> Version
        info = info or sys.version_info
        return Version(
            major=info[0],
            minor=info[1],
            patch=info[2]
        )

    @classmethod
    def _same_minor(cls, a, b):  # type: (Version, Version) -> bool
        return a.major == b.major and a.minor == b.minor

    @classmethod
    def _same_patch(cls, a, b):  # type: (Version, Version) -> bool
        return cls._same_minor(a, b) and a.patch == b.patch

    @classmethod
    def _exec_or_version_to_exec(cls, exec_or_version):  # type: (str) -> str
        try:
            version = Version.parse(exec_or_version)
            ret = "python{}".format(version.major)
            if version.precision > 1:
                ret += ".{}".format(version.minor)
            return ret
        except ValueError:
            # Executable in PATH or full executable path
            return exec_or_version

    @property
    def _root_venv_path(self):  # type: () -> Path
        return self._poetry.file.parent / ".venv"

    @property
    def _envs_file(self):  # type: () -> TomlFile
        return TomlFile(self._venvs_path / self.ENVS_FILE)

    @property
    def _venvs_path(self):  # type: () -> Path
        venv_path = self._poetry.config.get("virtualenvs.path")
        if venv_path is None:
            return Path(CACHE_DIR) / "virtualenvs"
        else:
            return Path(venv_path)

    # TODO - push defaults into config class
    @property
    def _create_venv(self):  # type: () -> bool
        return self._poetry.config.get("virtualenvs.create", True)

    @property
    def _root_venv(self):  # type: () -> bool
        return self._poetry.config.get("virtualenvs.in-project", False)


class Env(object):
    """
    An abstract Python environment.
    """

    def __init__(self, path, base=None):  # type: (Path, Optional[Path]) -> None
        self._is_windows = sys.platform == "win32"

        self._path = path
        bin_dir = "bin" if not self._is_windows else "Scripts"
        self._bin_dir = self._path / bin_dir

        self._base = base or path

        self._marker_env = None
        self._pip_version = None

    @property
    def path(self):  # type: () -> Path
        return self._path

    @property
    def base(self):  # type: () -> Path
        return self._base

    @property
    def version_info(self):  # type: () -> Tuple[int]
        return tuple(self.marker_env["version_info"])

    @property
    def python_implementation(self):  # type: () -> str
        return self.marker_env["platform_python_implementation"]

    @property
    def python(self):  # type: () -> str
        """
        Path to current python executable
        """
        return self._bin("python")

    @property
    def marker_env(self):
        if self._marker_env is None:
            self._marker_env = self.get_marker_env()

        return self._marker_env

    @property
    def pip(self):  # type: () -> str
        """
        Path to current pip executable
        """
        return self._bin("pip")

    @property
    def platform(self):  # type: () -> str
        return sys.platform

    @property
    def os(self):  # type: () -> str
        return os.name

    @property
    def pip_version(self):
        if self._pip_version is None:
            self._pip_version = self.get_pip_version()

        return self._pip_version

    @property
    def site_packages(self):  # type: () -> Path
        # It seems that PyPy3 virtual environments
        # have their site-packages directory at the root
        if self._path.joinpath("site-packages").exists():
            return self._path.joinpath("site-packages")

        if self._is_windows:
            return self._path / "Lib" / "site-packages"

        return (
            self._path
            / "lib"
            / "python{}.{}".format(*self.version_info[:2])
            / "site-packages"
        )

    @property
    def sys_path(self):  # type: () -> List[str]
        raise NotImplementedError()

    @classmethod
    def get_base_prefix(cls):  # type: () -> Path
        if hasattr(sys, "real_prefix"):
            return sys.real_prefix

        if hasattr(sys, "base_prefix"):
            return sys.base_prefix

        return sys.prefix

    def get_version_info(self):  # type: () -> Tuple[int]
        raise NotImplementedError()

    def get_python_implementation(self):  # type: () -> str
        raise NotImplementedError()

    def get_marker_env(self):  # type: () -> Dict[str, Any]
        raise NotImplementedError()

    def get_pip_command(self):  # type: () -> List[str]
        raise NotImplementedError()

    def config_var(self, var):  # type: (str) -> Any
        raise NotImplementedError()

    def get_pip_version(self):  # type: () -> Version
        raise NotImplementedError()

    def is_valid_for_marker(self, marker):  # type: (BaseMarker) -> bool
        return marker.validate(self.marker_env)

    def is_sane(self):  # type: () -> bool
        """
        Checks whether the current environment is sane or not.
        """
        return True

    def run(self, bin, *args, **kwargs):
        bin = self._bin(bin)
        cmd = [bin] + list(args)
        return self._run(cmd, **kwargs)

    def run_pip(self, *args, **kwargs):
        pip = self.get_pip_command()
        cmd = pip + list(args)
        return self._run(cmd, **kwargs)

    def _run(self, cmd, **kwargs):
        """
        Run a command inside the Python environment.
        """
        shell = kwargs.get("shell", False)
        call = kwargs.pop("call", False)
        input_ = kwargs.pop("input_", None)

        if shell:
            cmd = list_to_shell_command(cmd)
        try:
            if self._is_windows:
                kwargs["shell"] = True

            if input_:
                output = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    input=encode(input_),
                    check=True,
                    **kwargs
                ).stdout
            elif call:
                return subprocess.call(cmd, stderr=subprocess.STDOUT, **kwargs)
            else:
                output = subprocess.check_output(
                    cmd, stderr=subprocess.STDOUT, **kwargs
                )
        except CalledProcessError as e:
            raise EnvCommandError(e, input=input_)

        return decode(output)

    def execute(self, bin, *args, **kwargs):
        bin = self._bin(bin)

        if not self._is_windows:
            args = [bin] + list(args)
            if "env" in kwargs:
                return os.execvpe(bin, args, kwargs["env"])
            else:
                return os.execvp(bin, args)
        else:
            exe = subprocess.Popen([bin] + list(args), **kwargs)
            exe.communicate()
            return exe.returncode

    def is_venv(self):  # type: () -> bool
        raise NotImplementedError()

    def _bin(self, bin):  # type: (str) -> str
        """
        Return path to the given executable.
        """
        bin_path = (self._bin_dir / bin).with_suffix(".exe" if self._is_windows else "")
        if not bin_path.exists():
            # On Windows, some executables can be in the base path
            # This is especially true when installing Python with
            # the official installer, where python.exe will be at
            # the root of the env path.
            # This is an edge case and should not be encountered
            # in normal uses but this happens in the sonnet script
            # that creates a fake virtual environment pointing to
            # a base Python install.
            if self._is_windows:
                bin_path = (self._path / bin).with_suffix(".exe")
                if bin_path.exists():
                    return str(bin_path)

            return bin

        return str(bin_path)

    def __eq__(self, other):  # type: (Env) -> bool
        return other.__class__ == self.__class__ and other.path == self.path

    def __repr__(self):
        return '{}("{}")'.format(self.__class__.__name__, self._path)


class SystemEnv(Env):
    """
    A system (i.e. not a virtualenv) Python environment.
    """

    @property
    def sys_path(self):  # type: () -> List[str]
        return sys.path

    def get_version_info(self):  # type: () -> Tuple[int]
        return sys.version_info

    def get_python_implementation(self):  # type: () -> str
        return platform.python_implementation()

    def get_pip_command(self):  # type: () -> List[str]
        # If we're not in a venv, assume the interpreter we're running on
        # has a pip and use that
        return [sys.executable, "-m", "pip"]

    def get_marker_env(self):  # type: () -> Dict[str, Any]
        if hasattr(sys, "implementation"):
            info = sys.implementation.version
            iver = "{0.major}.{0.minor}.{0.micro}".format(info)
            kind = info.releaselevel
            if kind != "final":
                iver += kind[0] + str(info.serial)

            implementation_name = sys.implementation.name
        else:
            iver = "0"
            implementation_name = ""

        return {
            "implementation_name": implementation_name,
            "implementation_version": iver,
            "os_name": os.name,
            "platform_machine": platform.machine(),
            "platform_release": platform.release(),
            "platform_system": platform.system(),
            "platform_version": platform.version(),
            "python_full_version": platform.python_version(),
            "platform_python_implementation": platform.python_implementation(),
            "python_version": platform.python_version()[:3],
            "sys_platform": sys.platform,
            "version_info": sys.version_info,
        }

    def config_var(self, var):  # type: (str) -> Any
        try:
            return sysconfig.get_config_var(var)
        except IOError as e:
            warnings.warn("{0}".format(e), RuntimeWarning)

            return

    def get_pip_version(self):  # type: () -> Version
        from pip import __version__

        return Version.parse(__version__)

    def is_venv(self):  # type: () -> bool
        return self._path != self._base


class VirtualEnv(Env):
    """
    A virtual Python environment.
    """

    def __init__(self, path, base=None):  # type: (Path, Optional[Path]) -> None
        super(VirtualEnv, self).__init__(path, base)

        # If base is None, it probably means this is
        # a virtualenv created from VIRTUAL_ENV.
        # In this case we need to get sys.base_prefix
        # from inside the virtualenv.
        if base is None:
            self._base = Path(self.run("python", "-", input_=GET_BASE_PREFIX).strip())

    @property
    def sys_path(self):  # type: () -> List[str]
        output = self.run("python", "-", input_=GET_SYS_PATH)

        return json.loads(output)

    def get_version_info(self):  # type: () -> Tuple[int]
        output = self.run("python", "-", input_=GET_PYTHON_VERSION)

        return tuple([int(s) for s in output.strip().split(".")])

    def get_python_implementation(self):  # type: () -> str
        return self.marker_env["platform_python_implementation"]

    def get_pip_command(self):  # type: () -> List[str]
        # We're in a virtualenv that is known to be sane,
        # so assume that we have a functional pip
        return [self._bin("pip")]

    def get_marker_env(self):  # type: () -> Dict[str, Any]
        output = self.run("python", "-", input_=GET_ENVIRONMENT_INFO)

        return json.loads(output)

    def config_var(self, var):  # type: (str) -> Any
        try:
            value = self.run(
                "python", "-", input_=GET_CONFIG_VAR.format(config_var=var)
            ).strip()
        except EnvCommandError as e:
            warnings.warn("{0}".format(e), RuntimeWarning)
            return None

        if value == "None":
            value = None
        elif value == "1":
            value = 1
        elif value == "0":
            value = 0

        return value

    def get_pip_version(self):  # type: () -> Version
        output = self.run_pip("--version").strip()
        m = re.match("pip (.+?)(?: from .+)?$", output)
        if not m:
            return Version.parse("0.0")

        return Version.parse(m.group(1))

    def is_venv(self):  # type: () -> bool
        return True

    def is_sane(self):
        # A virtualenv is considered sane if both "python" and "pip" exist.
        return os.path.exists(self._bin("python")) and os.path.exists(self._bin("pip"))

    def _run(self, cmd, **kwargs):
        with self.temp_environ():
            os.environ["PATH"] = self._updated_path()
            os.environ["VIRTUAL_ENV"] = str(self._path)

            self.unset_env("PYTHONHOME")
            self.unset_env("__PYVENV_LAUNCHER__")

            return super(VirtualEnv, self)._run(cmd, **kwargs)

    def execute(self, bin, *args, **kwargs):
        with self.temp_environ():
            os.environ["PATH"] = self._updated_path()
            os.environ["VIRTUAL_ENV"] = str(self._path)

            self.unset_env("PYTHONHOME")
            self.unset_env("__PYVENV_LAUNCHER__")

            return super(VirtualEnv, self).execute(bin, *args, **kwargs)

    @contextmanager
    def temp_environ(self):
        environ = dict(os.environ)
        try:
            yield
        finally:
            os.environ.clear()
            os.environ.update(environ)

    def unset_env(self, key):
        if key in os.environ:
            del os.environ[key]

    def _updated_path(self):
        return os.pathsep.join([str(self._bin_dir), os.environ["PATH"]])


class NullEnv(SystemEnv):
    def __init__(self, path=None, base=None, execute=False):
        if path is None:
            path = Path(sys.prefix)

        super(NullEnv, self).__init__(path, base=base)

        self._execute = execute
        self.executed = []

    def _run(self, cmd, **kwargs):
        self.executed.append(cmd)

        if self._execute:
            return super(NullEnv, self)._run(cmd, **kwargs)

    def execute(self, bin, *args, **kwargs):
        self.executed.append([bin] + list(args))

        if self._execute:
            return super(NullEnv, self).execute(bin, *args, **kwargs)

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

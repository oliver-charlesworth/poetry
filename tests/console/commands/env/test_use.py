import os
import sys

import tomlkit

from cleo.testers import CommandTester

from poetry.semver import Version
from poetry.utils._compat import Path
from poetry.utils.env import EnvManager
from poetry.utils.toml_file import TomlFile
from tests.conftest import minimal_env_vars
from tests.mock_envs import MockEnv


def build_venv(path, executable=None):
    os.makedirs(path)


def check_output_wrapper(version=Version.parse("3.7.1")):
    def check_output(cmd, *args, **kwargs):
        if "sys.version_info[:3]" in cmd:
            return version.text
        elif "sys.version_info[:2]" in cmd:
            return "{}.{}".format(version.major, version.minor)
        else:
            return str(Path("/prefix"))

    return check_output


def test_activate_activates_non_existing_virtualenv_no_envs_file(
    app_factory, mocker, cache_dir
):
    app = app_factory(env_vars=minimal_env_vars(virtual_env=None))

    mocker.patch(
        "poetry.utils._compat.subprocess.check_output",
        side_effect=check_output_wrapper(),
    )
    mocker.patch(
        "poetry.utils._compat.subprocess.Popen.communicate",
        side_effect=[("/prefix", None), ("/prefix", None)],
    )
    m = mocker.patch("poetry.utils.env.EnvManager.build_venv", side_effect=build_venv)

    command = app.find("env use")
    tester = CommandTester(command)
    tester.execute("3.7")

    venv_name = EnvManager.generate_env_name(
        "simple-project", str(app.poetry.root)
    )

    expected_venvs_path = cache_dir / "virtualenvs"
    expected_venv_path = expected_venvs_path / "{}-py3.7".format(venv_name)

    m.assert_called_with(str(expected_venv_path), executable="python3.7")

    envs_file = TomlFile(expected_venvs_path / "envs.toml")
    assert envs_file.exists()
    envs = envs_file.read()
    assert envs[venv_name]["minor"] == "3.7"
    assert envs[venv_name]["patch"] == "3.7.1"

    expected = """\
Creating virtualenv {} in {}
Using virtualenv: {}
""".format(
        "{}-py3.7".format(venv_name),
        expected_venvs_path,
        expected_venv_path,
    )

    assert expected == tester.io.fetch_output()


def test_get_prefers_explicitly_activated_virtualenvs_over_env_var(
    app_factory, cache_dir, tmp_path
):
    app = app_factory(env_vars=minimal_env_vars(virtual_env=tmp_path))  # Explicitly set env var

    venv_name = EnvManager.generate_env_name(
        "simple-project", str(app.poetry.root)
    )
    current_python = sys.version_info[:3]
    python_minor = ".".join(str(v) for v in current_python[:2])
    python_patch = ".".join(str(v) for v in current_python)
    venvs_path = cache_dir / "virtualenvs"
    venv_path = venvs_path / "{}-py{}".format(venv_name, python_minor)

    os.makedirs(venv_path)  # Ensure it exists

    envs_file = TomlFile(venvs_path / "envs.toml")
    doc = tomlkit.document()
    doc[venv_name] = {"minor": python_minor, "patch": python_patch}
    envs_file.write(doc)

    command = app.find("env use")
    tester = CommandTester(command)
    tester.execute(python_minor)

    expected = """\
Using virtualenv: {}
""".format(venv_path)

    assert expected == tester.io.fetch_output()


def test_get_prefers_explicitly_activated_non_existing_virtualenvs_over_env_var(
    app_factory, mocker, cache_dir, tmp_path
):
    app = app_factory(env_vars=minimal_env_vars(virtual_env=tmp_path))  # Explicitly set env var

    venv_name = EnvManager.generate_env_name(
        "simple-project", str(app.poetry.root)
    )
    current_python = sys.version_info[:3]
    python_minor = ".".join(str(v) for v in current_python[:2])

    mocker.patch("poetry.utils.env.EnvManager.build_venv", side_effect=build_venv)

    command = app.find("env use")
    tester = CommandTester(command)
    tester.execute(python_minor)

    expected_venv_name = "{}-py{}".format(venv_name, python_minor)
    expected_venvs_path = cache_dir / "virtualenvs"
    expected_venv_path = expected_venvs_path / expected_venv_name

    expected = """\
Creating virtualenv {} in {}
Using virtualenv: {}
""".format(
        expected_venv_name,
        expected_venvs_path,
        expected_venv_path,
    )

    assert expected == tester.io.fetch_output()

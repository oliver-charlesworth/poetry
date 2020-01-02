import pytest
from cleo.testers import CommandTester

from poetry.utils._compat import Path
from poetry.utils.env import EnvManager

from .test_use import Version
from .test_use import check_output_wrapper


@pytest.fixture()
def manager(poetry):
    return EnvManager(poetry)


def test_remove_by_python_version(app, manager, tmp_dir, mocker):
    app.poetry.config.merge({"virtualenvs": {"path": str(tmp_dir)}})

    venv_name = manager.generate_env_name()
    (Path(tmp_dir) / "{}-py3.7".format(venv_name)).mkdir()
    (Path(tmp_dir) / "{}-py3.6".format(venv_name)).mkdir()

    check_output = mocker.patch(
        "poetry.utils._compat.subprocess.check_output",
        side_effect=check_output_wrapper(Version.parse("3.6.6")),
    )

    command = app.find("env remove")
    tester = CommandTester(command)
    tester.execute("3.6")

    assert check_output.called
    assert not (Path(tmp_dir) / "{}-py3.6".format(venv_name)).exists()

    expected = "Deleted virtualenv: {}\n".format(
        (Path(tmp_dir) / "{}-py3.6".format(venv_name))
    )

    assert expected == tester.io.fetch_output()


def test_remove_by_name(app, manager, tmp_dir):
    app.poetry.config.merge({"virtualenvs": {"path": str(tmp_dir)}})

    venv_name = manager.generate_env_name()
    (Path(tmp_dir) / "{}-py3.7".format(venv_name)).mkdir()
    (Path(tmp_dir) / "{}-py3.6".format(venv_name)).mkdir()

    command = app.find("env remove")
    tester = CommandTester(command)
    tester.execute("{}-py3.6".format(venv_name))

    assert not (Path(tmp_dir) / "{}-py3.6".format(venv_name)).exists()

    expected = "Deleted virtualenv: {}\n".format(
        (Path(tmp_dir) / "{}-py3.6".format(venv_name))
    )

    assert expected == tester.io.fetch_output()

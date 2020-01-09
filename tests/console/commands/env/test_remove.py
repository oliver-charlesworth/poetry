from cleo.testers import CommandTester

from poetry.utils._compat import Path
from poetry.utils.env import EnvManager

from .test_use import Version
from .test_use import check_output_wrapper


def test_remove_by_python_version(app_factory, tmp_path, mocker):
    app = app_factory()

    app.poetry.config.merge({"virtualenvs": {"path": str(tmp_path)}})

    venv_name = EnvManager.generate_env_name(
        "simple-project", str(app.poetry.root)
    )
    (tmp_path / "{}-py3.7".format(venv_name)).mkdir()
    (tmp_path / "{}-py3.6".format(venv_name)).mkdir()

    check_output = mocker.patch(
        "poetry.utils._compat.subprocess.check_output",
        side_effect=check_output_wrapper(Version.parse("3.6.6")),
    )

    command = app.find("env remove")
    tester = CommandTester(command)
    tester.execute("3.6")

    assert check_output.called
    assert not (tmp_path / "{}-py3.6".format(venv_name)).exists()

    expected = "Deleted virtualenv: {}\n".format(
        (tmp_path / "{}-py3.6".format(venv_name))
    )

    assert expected == tester.io.fetch_output()


def test_remove_by_name(app_factory, cache_dir):
    app = app_factory()
    manager = EnvManager(app.poetry)

    venv_name = manager.generate_env_name("simple-project", str(app.poetry.root))
    venvs_path = cache_dir / "virtualenvs"
    venv_path_37 = venvs_path / "{}-py3.7".format(venv_name)
    venv_path_36 = venvs_path / "{}-py3.6".format(venv_name)

    manager.build_venv(venv_path_37)
    manager.build_venv(venv_path_36)

    command = app.find("env remove")
    tester = CommandTester(command)
    tester.execute("{}-py3.6".format(venv_name))

    assert not venv_path_36.exists()

    expected = "Deleted virtualenv: {}\n".format(venv_path_36)

    assert expected == tester.io.fetch_output()

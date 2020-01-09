import tomlkit

from cleo.testers import CommandTester

from poetry.utils.env import EnvManager
from poetry.utils.toml_file import TomlFile


def test_none_activated(app_factory, cache_dir):
    app = app_factory()
    manager = EnvManager(app.poetry)

    venv_name = manager.generate_env_name("simple-project", str(app.poetry.root))
    venvs_path = cache_dir / "virtualenvs"
    venv_path_37 = venvs_path / "{}-py3.7".format(venv_name)
    venv_path_36 = venvs_path / "{}-py3.6".format(venv_name)

    manager.build_venv(venv_path_37)
    manager.build_venv(venv_path_36)

    command = app.find("env list")
    tester = CommandTester(command)
    tester.execute()

    expected = """\
{}-py3.6
{}-py3.7
""".format(
        venv_name, venv_name
    )

    assert expected == tester.io.fetch_output()


def test_activated(app_factory, cache_dir):
    app = app_factory()

    manager = EnvManager(app.poetry)

    venv_name = manager.generate_env_name("simple-project", str(app.poetry.root))
    venvs_path = cache_dir / "virtualenvs"
    venv_path_37 = venvs_path / "{}-py3.7".format(venv_name)
    venv_path_36 = venvs_path / "{}-py3.6".format(venv_name)

    manager.build_venv(venv_path_37)
    manager.build_venv(venv_path_36)

    envs_file = TomlFile(venvs_path / "envs.toml")
    doc = tomlkit.document()
    doc[venv_name] = {"minor": "3.7", "patch": "3.7.0"}
    envs_file.write(doc)

    command = app.find("env list")
    tester = CommandTester(command)
    tester.execute()

    expected = """\
{}-py3.6
{}-py3.7 (Activated)
""".format(
        venv_name, venv_name
    )

    assert expected == tester.io.fetch_output()

import os

from poetry.config.config import Config


def test_config_get_default_value(config):
    assert config.get("virtualenvs.create") is True


def test_config_get_processes_depended_on_values(config):
    assert os.path.join("/foo", "virtualenvs") == config.get("virtualenvs.path")


def test_config_get_from_environment_variable():
    config = Config(env_vars={})

    assert config.get("virtualenvs.create")

    config = Config(env_vars={
        "POETRY_VIRTUALENVS_CREATE": "false"
    })

    assert not config.get("virtualenvs.create")

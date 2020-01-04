import json
import os

import pytest
from cleo.testers import CommandTester

from poetry.config.config_source import ConfigSource


def test_list_displays_default_value_if_not_set(app_factory, config):
    app = app_factory()

    command = app.find("config")
    tester = CommandTester(command)
    tester.execute("--list")

    expected = """cache-dir = "/foo"
virtualenvs.create = true
virtualenvs.in-project = false
virtualenvs.path = {path}  # /foo{sep}virtualenvs
""".format(
        path=json.dumps(os.path.join("{cache-dir}", "virtualenvs")), sep=os.path.sep
    )

    assert expected == tester.io.fetch_output()


def test_list_displays_set_get_setting(app_factory, config):
    app = app_factory()

    command = app.find("config")
    tester = CommandTester(command)

    tester.execute("virtualenvs.create false")

    tester.execute("--list")

    expected = """cache-dir = "/foo"
virtualenvs.create = false
virtualenvs.in-project = false
virtualenvs.path = {path}  # /foo{sep}virtualenvs
""".format(
        path=json.dumps(os.path.join("{cache-dir}", "virtualenvs")), sep=os.path.sep
    )

    assert 0 == config.set_config_source.call_count
    assert expected == tester.io.fetch_output()


def test_display_single_setting(app_factory, config):
    app = app_factory()

    command = app.find("config")
    tester = CommandTester(command)

    tester.execute("virtualenvs.create")

    expected = """true
"""

    assert expected == tester.io.fetch_output()


@pytest.mark.parametrize("project_directory", ["with_local_config"])
def test_display_single_local_setting(app_factory, config):
    app = app_factory()

    # poetry = poetry_factory("with_local_config", is_root_fixture=True)
    # app._poetry = poetry  # TODO - can we do better?

    command = app.find("config")
    tester = CommandTester(command)

    tester.execute("virtualenvs.create")

    expected = """false
"""

    assert expected == tester.io.fetch_output()


def test_list_displays_set_get_local_setting(app_factory, config):
    app = app_factory()

    command = app.find("config")
    tester = CommandTester(command)

    tester.execute("virtualenvs.create false --local")

    tester.execute("--list")

    expected = """cache-dir = "/foo"
virtualenvs.create = false
virtualenvs.in-project = false
virtualenvs.path = {path}  # /foo{sep}virtualenvs
""".format(
        path=json.dumps(os.path.join("{cache-dir}", "virtualenvs")), sep=os.path.sep
    )

    assert 1 == config.set_config_source.call_count
    assert expected == tester.io.fetch_output()


def test_set_pypi_token(app_factory, config, config_source, auth_config_source):
    app = app_factory()

    command = app.find("config")
    tester = CommandTester(command)

    tester.execute("pypi-token.pypi mytoken")

    tester.execute("--list")

    assert "mytoken" == auth_config_source.config["pypi-token"]["pypi"]


def test_set_client_cert(app_factory, config_source, auth_config_source, mocker):
    app = app_factory()

    mocker.spy(ConfigSource, "__init__")
    command = app.find("config")
    tester = CommandTester(command)

    tester.execute("certificates.foo.client-cert path/to/cert.pem")

    assert (
        "path/to/cert.pem"
        == auth_config_source.config["certificates"]["foo"]["client-cert"]
    )


def test_set_cert(app_factory, config_source, auth_config_source, mocker):
    app = app_factory()

    mocker.spy(ConfigSource, "__init__")
    command = app.find("config")
    tester = CommandTester(command)

    tester.execute("certificates.foo.cert path/to/ca.pem")

    assert "path/to/ca.pem" == auth_config_source.config["certificates"]["foo"]["cert"]

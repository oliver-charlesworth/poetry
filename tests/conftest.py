import os
import shutil
import subprocess
import tempfile

from typing import Any
from typing import Dict
from typing import Optional

import httpretty
import pytest

from poetry.config.config import Config as BaseConfig
from poetry.config.dict_config_source import DictConfigSource
from poetry.factory import Factory
from poetry.poetry import Poetry
from poetry.utils._compat import Path
from tests.helpers import mock_clone
from tests.helpers import mock_download


# TODO - what is the point of this?
class Config(BaseConfig):
    def __init__(self, env_vars):
        super(Config, self).__init__(env_vars=env_vars)

    def get(self, setting_name, default=None):  # type: (str, Any) -> Any
        self.merge(self._config_source.config)
        self.merge(self._auth_config_source.config)

        return super(Config, self).get(setting_name, default=default)

    def raw(self):  # type: () -> Dict[str, Any]
        self.merge(self._config_source.config)
        self.merge(self._auth_config_source.config)

        return super(Config, self).raw()

    def all(self):  # type: () -> Dict[str, Any]
        self.merge(self._config_source.config)
        self.merge(self._auth_config_source.config)

        return super(Config, self).all()


@pytest.fixture
def config_source():
    source = DictConfigSource()
    source.add_property("cache-dir", "/foo")

    return source


@pytest.fixture
def auth_config_source():
    source = DictConfigSource()

    return source


@pytest.fixture
def config(config_source, auth_config_source, mocker):
    import keyring
    from keyring.backends.fail import Keyring

    keyring.set_keyring(Keyring())

    c = Config(env_vars={})
    c.merge(config_source.config)
    c.set_config_source(config_source)
    c.set_auth_config_source(auth_config_source)

    mocker.patch("poetry.factory.Factory.create_config", return_value=c)
    mocker.patch("poetry.config.config.Config.set_config_source")

    return c


@pytest.fixture(autouse=True)
def download_mock(mocker):
    # Patch download to not download anything but to just copy from fixtures
    mocker.patch("poetry.utils.inspector.Inspector.download", new=mock_download)


@pytest.fixture(autouse=True)
def git_mock(mocker):
    # Patch git module to not actually clone projects
    mocker.patch("poetry.vcs.git.Git.clone", new=mock_clone)
    mocker.patch("poetry.vcs.git.Git.checkout", new=lambda *_: None)
    p = mocker.patch("poetry.vcs.git.Git.rev_parse")
    p.return_value = "9cf87a285a2d3fbb0b9fa621997b3acc3631ed24"


@pytest.fixture
def http():
    httpretty.enable()

    yield httpretty

    httpretty.disable()


@pytest.fixture
def tmp_dir():
    dir_ = tempfile.mkdtemp(prefix="poetry_")

    yield dir_

    shutil.rmtree(dir_)


@pytest.fixture
def fixtures_dir(request, tmp_path_factory):
    def _reference_path(relative_to_root):  # type: (str) -> Path
        if relative_to_root is None:
            return Path(request.module.__file__).parent
        else:
            return Path(__file__).parent / relative_to_root  # Relies on *this* conftest file being in the tests/ root

    # Test cases may mutate things, so encapsulate by making a copy of the fixtures
    def _create(relative_to_root=None):  # type: (str) -> Path
        source = _reference_path(relative_to_root) / "fixtures"
        target = tmp_path_factory.mktemp("target", numbered=True) / "fixtures"

        shutil.copytree(source.as_posix(), target.as_posix())

        return target

    return _create


def minimal_env_vars(
    path=os.environ["PATH"], virtual_env=os.environ["VIRTUAL_ENV"], **kwargs
):
    env = dict(kwargs)
    if path:
        env["PATH"] = path
    if virtual_env:
        env["VIRTUAL_ENV"] = virtual_env
    return env


@pytest.fixture
def poetry_factory(fixtures_dir):
    factory = Factory()

    # Tests generally rely on fixtures looking like a Git repo
    def _init_as_git_repo(path):  # type: (Path) -> None
        subprocess.check_output(["git", "init"], cwd=path.as_posix())

    def _create(
        name, relative_to_root=None, env_vars=None
    ):  # type: (str, bool, Optional[Dict[str, str]]) -> Poetry
        path = fixtures_dir(relative_to_root) / name

        _init_as_git_repo(path)

        return factory.create_poetry(env_vars=env_vars or minimal_env_vars(), cwd=path)

    return _create

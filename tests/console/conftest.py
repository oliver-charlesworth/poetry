import os

import pytest

from cleo import ApplicationTester

from poetry.console import Application as BaseApplication
from poetry.factory import Factory
from poetry.installation.noop_installer import NoopInstaller
from poetry.packages import Locker as BaseLocker
from poetry.repositories import Pool
from poetry.repositories import Repository as BaseRepository
from poetry.repositories.exceptions import PackageNotFound
from poetry.utils.toml_file import TomlFile
from tests.conftest import minimal_env
from tests.helpers import mock_clone
from tests.helpers import mock_download


@pytest.fixture()
def installer():
    return NoopInstaller()


@pytest.fixture
def installed():
    return BaseRepository()


@pytest.fixture(autouse=True)
def setup(mocker, installer, installed, config):
    # Set Installer's installer
    p = mocker.patch("poetry.installation.installer.Installer._get_installer")
    p.return_value = installer

    p = mocker.patch("poetry.installation.installer.Installer._get_installed")
    p.return_value = installed

    p = mocker.patch(
        "poetry.repositories.installed_repository.InstalledRepository.load"
    )
    p.return_value = installed

    # Patch git module to not actually clone projects
    mocker.patch("poetry.vcs.git.Git.clone", new=mock_clone)
    mocker.patch("poetry.vcs.git.Git.checkout", new=lambda *_: None)
    p = mocker.patch("poetry.vcs.git.Git.rev_parse")
    p.return_value = "9cf87a285a2d3fbb0b9fa621997b3acc3631ed24"

    # Patch download to not download anything but to just copy from fixtures
    mocker.patch("poetry.utils.inspector.Inspector.download", new=mock_download)


class Application(BaseApplication):
    def __init__(self, poetry):
        super(Application, self).__init__(poetry.env)

        self._poetry = poetry

    def reset_poetry(self):
        poetry = self._poetry
        self._poetry = Factory().create_poetry(env=poetry.env, cwd=poetry.file.path.parent)
        self._poetry.set_pool(poetry.pool)
        self._poetry.set_config(poetry.config)
        self._poetry.set_locker(poetry.locker)


class Locker(BaseLocker):
    def __init__(self, lock, local_config):
        self._lock = TomlFile(lock)
        self._local_config = local_config
        self._lock_data = None
        self._content_hash = self._get_content_hash()
        self._locked = False
        self._lock_data = None
        self._write = True

    def write(self, write=True):
        self._write = write

    def is_locked(self):
        return self._locked

    def locked(self, is_locked=True):
        self._locked = is_locked

        return self

    def mock_lock_data(self, data):
        self.locked()

        self._lock_data = data

    def is_fresh(self):
        return True

    def _write_lock_data(self, data):
        if self._write:
            super(Locker, self)._write_lock_data(data)
            self._locked = True
            return

        self._lock_data = None


class Repository(BaseRepository):
    def find_packages(
        self, name, constraint=None, extras=None, allow_prereleases=False
    ):
        packages = super(Repository, self).find_packages(
            name, constraint, extras, allow_prereleases
        )
        if len(packages) == 0:
            raise PackageNotFound("Package [{}] not found.".format(name))
        return packages


@pytest.fixture
def repo():
    return Repository()


@pytest.fixture
def app_factory(poetry_factory, repo, config):
    def _create_poetry(name, env):
        p = poetry_factory(name, is_root_fixture=True, env=env)
        p.set_locker(Locker(p.locker.lock.path, p.locker._local_config))

        p.set_config(config)

        pool = Pool()
        pool.add_repository(repo)
        p.set_pool(pool)

        return p

    def _create(name="simple_project", env=None):
        poetry = _create_poetry(name, env or minimal_env())
        app = Application(poetry)
        app.config.set_terminate_after_run(False)

        return app

    return _create

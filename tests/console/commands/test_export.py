# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from cleo.testers import CommandTester

from tests.helpers import get_package


@pytest.fixture
def app(app_factory):
    return app_factory(name="project_for_exporting")


def test_export_exports_requirements_txt_file_locks_if_no_lock_file(app, repo):
    command = app.find("export")
    tester = CommandTester(command)

    assert not app.poetry.locker.lock.exists()

    repo.add_package(get_package("foo", "1.0.0"))
    repo.add_package(get_package("bar", "1.1.0"))

    tester.execute("--format requirements.txt --output requirements.txt")

    requirements = app.poetry.root / "requirements.txt"
    assert requirements.exists()

    with requirements.open(encoding="utf-8") as f:
        content = f.read()

    assert app.poetry.locker.lock.exists()

    expected = """\
foo==1.0.0
"""

    assert expected == content
    assert "The lock file does not exist. Locking." in tester.io.fetch_output()


def test_export_exports_requirements_txt_uses_lock_file(app, repo):
    repo.add_package(get_package("foo", "1.0.0"))
    repo.add_package(get_package("bar", "1.1.0"))

    command = app.find("lock")
    tester = CommandTester(command)
    tester.execute()

    assert app.poetry.locker.lock.exists()

    command = app.find("export")
    tester = CommandTester(command)

    tester.execute("--format requirements.txt --output requirements.txt")

    requirements = app.poetry.root / "requirements.txt"
    assert requirements.exists()

    with requirements.open(encoding="utf-8") as f:
        content = f.read()

    assert app.poetry.locker.lock.exists()

    expected = """\
foo==1.0.0
"""

    assert expected == content
    assert "The lock file does not exist. Locking." not in tester.io.fetch_output()


def test_export_fails_on_invalid_format(app, repo):
    repo.add_package(get_package("foo", "1.0.0"))
    repo.add_package(get_package("bar", "1.1.0"))

    command = app.find("lock")
    tester = CommandTester(command)
    tester.execute()

    assert app.poetry.locker.lock.exists()

    command = app.find("export")
    tester = CommandTester(command)

    with pytest.raises(ValueError):
        tester.execute("--format invalid")


def test_export_prints_to_stdout_by_default(app, repo):
    repo.add_package(get_package("foo", "1.0.0"))
    repo.add_package(get_package("bar", "1.1.0"))

    command = app.find("lock")
    tester = CommandTester(command)
    tester.execute()

    assert app.poetry.locker.lock.exists()

    command = app.find("export")
    tester = CommandTester(command)

    tester.execute("--format requirements.txt")

    expected = """\
foo==1.0.0
"""

    assert expected == tester.io.fetch_output()


def test_export_includes_extras_by_flag(app, repo):
    repo.add_package(get_package("foo", "1.0.0"))
    repo.add_package(get_package("bar", "1.1.0"))

    command = app.find("lock")
    tester = CommandTester(command)
    tester.execute()

    assert app.poetry.locker.lock.exists()

    command = app.find("export")
    tester = CommandTester(command)

    tester.execute("--format requirements.txt --extras feature_bar")

    expected = """\
bar==1.1.0
foo==1.0.0
"""

    assert expected == tester.io.fetch_output()

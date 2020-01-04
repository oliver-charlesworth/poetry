import pytest

from cleo.testers import CommandTester
from clikit.formatter.ansi_formatter import AnsiFormatter

from tests.conftest import minimal_env_vars
from tests.helpers import get_package


_MINIMAL_ENV_VARS = minimal_env_vars(COLUMNS="80")  # Fix terminal width


def test_show_basic_with_installed_packages(app_factory, installed):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    pytest_373 = get_package("pytest", "3.7.3")
    pytest_373.description = "Pytest package"
    pytest_373.category = "dev"

    installed.add_package(cachy_010)
    installed.add_package(pendulum_200)
    installed.add_package(pytest_373)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pytest",
                    "version": "3.7.3",
                    "description": "Pytest package",
                    "category": "dev",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": [], "pytest": []},
            },
        }
    )

    tester.execute()

    expected = """\
cachy    0.1.0 Cachy package
pendulum 2.0.0 Pendulum package
pytest   3.7.3 Pytest package
"""

    assert expected == tester.io.fetch_output()


def test_show_basic_with_not_installed_packages_non_decorated(app_factory, installed):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    installed.add_package(cachy_010)
    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": []},
            },
        }
    )

    tester.execute()

    expected = """\
cachy        0.1.0 Cachy package
pendulum (!) 2.0.0 Pendulum package
"""

    assert expected == tester.io.fetch_output()


def test_show_basic_with_not_installed_packages_decorated(app_factory, installed):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    installed.add_package(cachy_010)
    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": []},
            },
        }
    )

    tester.io.set_formatter(AnsiFormatter(forced=True))
    tester.execute()

    expected = """\
\033[36mcachy   \033[0m \033[1m0.1.0\033[0m Cachy package
\033[31mpendulum\033[0m \033[1m2.0.0\033[0m Pendulum package
"""

    assert expected == tester.io.fetch_output()


def test_show_latest_non_decorated(app_factory, installed, repo):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"
    cachy_020 = get_package("cachy", "0.2.0")
    cachy_020.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"
    pendulum_201 = get_package("pendulum", "2.0.1")
    pendulum_201.description = "Pendulum package"

    installed.add_package(cachy_010)
    installed.add_package(pendulum_200)

    repo.add_package(cachy_010)
    repo.add_package(cachy_020)
    repo.add_package(pendulum_200)
    repo.add_package(pendulum_201)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": []},
            },
        }
    )

    tester.execute("--latest")

    expected = """\
cachy    0.1.0 0.2.0 Cachy package
pendulum 2.0.0 2.0.1 Pendulum package
"""

    assert expected == tester.io.fetch_output()


def test_show_latest_decorated(app_factory, installed, repo):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"
    cachy_020 = get_package("cachy", "0.2.0")
    cachy_020.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"
    pendulum_201 = get_package("pendulum", "2.0.1")
    pendulum_201.description = "Pendulum package"

    installed.add_package(cachy_010)
    installed.add_package(pendulum_200)

    repo.add_package(cachy_010)
    repo.add_package(cachy_020)
    repo.add_package(pendulum_200)
    repo.add_package(pendulum_201)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": []},
            },
        }
    )

    tester.io.set_formatter(AnsiFormatter(forced=True))
    tester.execute("--latest")

    expected = """\
\033[36mcachy   \033[0m \033[1m0.1.0\033[0m \033[33m0.2.0\033[0m Cachy package
\033[36mpendulum\033[0m \033[1m2.0.0\033[0m \033[31m2.0.1\033[0m Pendulum package
"""

    assert expected == tester.io.fetch_output()


def test_show_outdated(app_factory, installed, repo):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"
    cachy_020 = get_package("cachy", "0.2.0")
    cachy_020.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    installed.add_package(cachy_010)
    installed.add_package(pendulum_200)

    repo.add_package(cachy_010)
    repo.add_package(cachy_020)
    repo.add_package(pendulum_200)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": []},
            },
        }
    )

    tester.execute("--outdated")

    expected = """\
cachy 0.1.0 0.2.0 Cachy package
"""

    assert expected == tester.io.fetch_output()


def test_show_outdated_with_only_up_to_date_packages(app_factory, installed, repo):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_020 = get_package("cachy", "0.2.0")
    cachy_020.description = "Cachy package"

    installed.add_package(cachy_020)
    repo.add_package(cachy_020)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.2.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": []},
            },
        }
    )

    tester.execute("--outdated")

    expected = ""

    assert expected == tester.io.fetch_output()


def test_show_outdated_has_prerelease_but_not_allowed(app_factory, installed, repo):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"
    cachy_020 = get_package("cachy", "0.2.0")
    cachy_020.description = "Cachy package"
    cachy_030dev = get_package("cachy", "0.3.0.dev123")
    cachy_030dev.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    installed.add_package(cachy_010)
    installed.add_package(pendulum_200)

    # sorting isn't used, so this has to be the first element to
    # replicate the issue in PR #1548
    repo.add_package(cachy_030dev)
    repo.add_package(cachy_010)
    repo.add_package(cachy_020)
    repo.add_package(pendulum_200)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": []},
            },
        }
    )

    tester.execute("--outdated")

    expected = """\
cachy 0.1.0 0.2.0 Cachy package
"""

    assert expected == tester.io.fetch_output()


def test_show_outdated_has_prerelease_and_allowed(app_factory, installed, repo):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010dev = get_package("cachy", "0.1.0.dev1")
    cachy_010dev.description = "Cachy package"
    cachy_020 = get_package("cachy", "0.2.0")
    cachy_020.description = "Cachy package"
    cachy_030dev = get_package("cachy", "0.3.0.dev123")
    cachy_030dev.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    installed.add_package(cachy_010dev)
    installed.add_package(pendulum_200)

    # sorting isn't used, so this has to be the first element to
    # replicate the issue in PR #1548
    repo.add_package(cachy_030dev)
    repo.add_package(cachy_010dev)
    repo.add_package(cachy_020)
    repo.add_package(pendulum_200)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0.dev1",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": []},
            },
        }
    )

    tester.execute("--outdated")

    expected = """\
cachy 0.1.0.dev1 0.3.0.dev123 Cachy package
"""

    assert expected == tester.io.fetch_output()


def test_show_outdated_formatting(app_factory, installed, repo):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"
    cachy_020 = get_package("cachy", "0.2.0")
    cachy_020.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"
    pendulum_201 = get_package("pendulum", "2.0.1")
    pendulum_201.description = "Pendulum package"

    installed.add_package(cachy_010)
    installed.add_package(pendulum_200)

    repo.add_package(cachy_010)
    repo.add_package(cachy_020)
    repo.add_package(pendulum_200)
    repo.add_package(pendulum_201)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": []},
            },
        }
    )

    tester.execute("--outdated")

    expected = """\
cachy    0.1.0 0.2.0 Cachy package
pendulum 2.0.0 2.0.1 Pendulum package
"""

    assert expected == tester.io.fetch_output()


def test_show_outdated_local_dependencies(app_factory, installed, repo):
    app = app_factory("project_with_local_dependencies", env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"
    cachy_020 = get_package("cachy", "0.2.0")
    cachy_020.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    demo_010 = get_package("demo", "0.1.0")
    demo_010.description = ""

    my_package_012 = get_package("my-package", "0.1.2")
    my_package_012.description = "Demo project."

    installed.add_package(cachy_010)
    installed.add_package(pendulum_200)
    installed.add_package(demo_010)
    installed.add_package(my_package_012)

    repo.add_package(cachy_010)
    repo.add_package(cachy_020)
    repo.add_package(pendulum_200)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "demo",
                    "version": "0.1.0",
                    "description": "Demo package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                    "source": {
                        "type": "file",
                        "reference": "",
                        "url": "../distributions/demo-0.1.0-py2.py3-none-any.whl",
                    },
                },
                {
                    "name": "my-package",
                    "version": "0.1.1",
                    "description": "Demo project.",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                    "source": {
                        "type": "directory",
                        "reference": "",
                        "url": "../project_with_setup",
                    },
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": [], "demo": [], "my-package": []},
            },
        }
    )

    tester.execute("--outdated")

    expected = """\
cachy      0.1.0                       0.2.0
my-package 0.1.1 ../project_with_setup 0.1.2 ../project_with_setup
"""
    assert expected.rstrip() == "\n".join(
        l.rstrip() for l in tester.io.fetch_output().splitlines()
    )


def test_show_outdated_git_dev_dependency(app_factory, installed, repo):
    app = app_factory("project_with_git_dev_dependency", env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"
    cachy_020 = get_package("cachy", "0.2.0")
    cachy_020.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    demo_011 = get_package("demo", "0.1.1")
    demo_011.description = "Demo package"

    installed.add_package(cachy_010)
    installed.add_package(pendulum_200)
    installed.add_package(demo_011)

    repo.add_package(cachy_010)
    repo.add_package(cachy_020)
    repo.add_package(pendulum_200)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "demo",
                    "version": "0.1.1",
                    "description": "Demo package",
                    "category": "dev",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                    "source": {
                        "type": "git",
                        "reference": "9cf87a285a2d3fbb0b9fa621997b3acc3631ed24",
                        "url": "https://github.com/demo/pyproject-demo.git",
                    },
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": [], "demo": []},
            },
        }
    )

    tester.execute("--outdated")

    expected = """\
cachy 0.1.0         0.2.0         Cachy package
demo  0.1.1 9cf87a2 0.1.2 9cf87a2 Demo package
"""

    assert expected == tester.io.fetch_output()


def test_show_outdated_no_dev_git_dev_dependency(app_factory, installed, repo):
    app = app_factory("project_with_git_dev_dependency", env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"
    cachy_020 = get_package("cachy", "0.2.0")
    cachy_020.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    demo_011 = get_package("demo", "0.1.1")
    demo_011.description = "Demo package"

    installed.add_package(cachy_010)
    installed.add_package(pendulum_200)
    installed.add_package(demo_011)

    repo.add_package(cachy_010)
    repo.add_package(cachy_020)
    repo.add_package(pendulum_200)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "demo",
                    "version": "0.1.1",
                    "description": "Demo package",
                    "category": "dev",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                    "source": {
                        "type": "git",
                        "reference": "9cf87a285a2d3fbb0b9fa621997b3acc3631ed24",
                        "url": "https://github.com/demo/pyproject-demo.git",
                    },
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": [], "demo": []},
            },
        }
    )

    tester.execute("--outdated --no-dev")

    expected = """\
cachy 0.1.0 0.2.0 Cachy package
"""

    assert expected == tester.io.fetch_output()


def test_show_hides_incompatible_package(app_factory, installed, repo):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    installed.add_package(pendulum_200)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                    "requirements": {"python": "1.0"},
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": []},
            },
        }
    )

    tester.execute()

    expected = """\
pendulum 2.0.0 Pendulum package
"""

    assert expected == tester.io.fetch_output()


def test_show_all_shows_incompatible_package(app_factory, installed, repo):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    installed.add_package(pendulum_200)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                    "requirements": {"python": "1.0"},
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": []},
            },
        }
    )

    tester.execute("--all")

    expected = """\
cachy     0.1.0 Cachy package
pendulum  2.0.0 Pendulum package
"""

    assert expected == tester.io.fetch_output()


def test_show_non_dev_with_basic_installed_packages(app_factory, installed):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    cachy_010 = get_package("cachy", "0.1.0")
    cachy_010.description = "Cachy package"

    pendulum_200 = get_package("pendulum", "2.0.0")
    pendulum_200.description = "Pendulum package"

    pytest_373 = get_package("pytest", "3.7.3")
    pytest_373.description = "Pytest package"
    pytest_373.category = "dev"

    installed.add_package(cachy_010)
    installed.add_package(pendulum_200)
    installed.add_package(pytest_373)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.1.0",
                    "description": "Cachy package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pendulum",
                    "version": "2.0.0",
                    "description": "Pendulum package",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
                {
                    "name": "pytest",
                    "version": "3.7.3",
                    "description": "Pytest package",
                    "category": "dev",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "pendulum": [], "pytest": []},
            },
        }
    )

    tester.execute("--no-dev")

    expected = """\
cachy    0.1.0 Cachy package
pendulum 2.0.0 Pendulum package
"""

    assert expected == tester.io.fetch_output()


def test_show_tree(app_factory, installed):
    app = app_factory(env_vars=_MINIMAL_ENV_VARS)

    command = app.find("show")
    tester = CommandTester(command)

    app.poetry.package.add_dependency("cachy", "^0.2.0")

    cachy2 = get_package("cachy", "0.2.0")
    cachy2.add_dependency("msgpack-python", ">=0.5 <0.6")

    installed.add_package(cachy2)

    app.poetry.locker.mock_lock_data(
        {
            "package": [
                {
                    "name": "cachy",
                    "version": "0.2.0",
                    "description": "",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                    "dependencies": {"msgpack-python": ">=0.5 <0.6"},
                },
                {
                    "name": "msgpack-python",
                    "version": "0.5.1",
                    "description": "",
                    "category": "main",
                    "optional": False,
                    "platform": "*",
                    "python-versions": "*",
                    "checksum": [],
                },
            ],
            "metadata": {
                "python-versions": "*",
                "platform": "*",
                "content-hash": "123456789",
                "hashes": {"cachy": [], "msgpack-python": []},
            },
        }
    )

    tester.execute("--tree")

    expected = """\
cachy 0.2.0
`-- msgpack-python >=0.5 <0.6
"""

    assert expected == tester.io.fetch_output()

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys

from clikit.io import NullIO

from poetry.masonry.builders import EditableBuilder
from poetry.utils._compat import Path
from tests.mock_envs import MockEnv


def test_build_should_delegate_to_pip_for_non_pure_python_packages(poetry_factory, tmp_dir, mocker):
    move = mocker.patch("shutil.move")
    tmp_dir = Path(tmp_dir)
    env = MockEnv(path=tmp_dir, pip_version="18.1", execute=False)
    env.site_packages.mkdir(parents=True)
    poetry = poetry_factory("extended")

    builder = EditableBuilder(poetry, env, NullIO())
    builder.build()

    expected = [[sys.executable, "-m", "pip", "install", "-e", str(poetry.file.parent)]]
    assert expected == env.executed

    assert 0 == move.call_count


def test_build_should_temporarily_remove_the_pyproject_file(poetry_factory, tmp_dir, mocker):
    move = mocker.patch("shutil.move")
    tmp_dir = Path(tmp_dir)
    env = MockEnv(path=tmp_dir, pip_version="19.1", execute=False)
    env.site_packages.mkdir(parents=True)
    poetry = poetry_factory("extended")

    builder = EditableBuilder(poetry, env, NullIO())
    builder.build()

    expected = [[sys.executable, "-m", "pip", "install", "-e", str(poetry.file.parent)]]
    assert expected == env.executed

    assert 2 == move.call_count

    expected_calls = [
        mocker.call(
            str(poetry.file.parent / "pyproject.toml"), str(poetry.file.parent / "pyproject.tmp")
        ),
        mocker.call(
            str(poetry.file.parent / "pyproject.tmp"), str(poetry.file.parent / "pyproject.toml")
        ),
    ]

    assert expected_calls == move.call_args_list

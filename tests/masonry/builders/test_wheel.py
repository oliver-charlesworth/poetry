# -*- coding: utf-8 -*-
import os
import shutil
import zipfile

import pytest

from clikit.io import NullIO

from poetry.factory import Factory
from poetry.masonry.builders.wheel import WheelBuilder
from poetry.masonry.publishing.uploader import Uploader
from poetry.utils._compat import Path
from tests.mock_envs import NullEnv


fixtures_dir = Path(__file__).parent / "fixtures"


def poetry_for(name):
    return Factory().create_poetry(
        env=os.environ,
        cwd=Path(__file__).parent / "fixtures" / name
    )


@pytest.fixture(autouse=True)
def setup():
    clear_samples_dist()

    yield

    clear_samples_dist()


# TODO - need to implement copy-to-tmp mechanism
def clear_samples_dist():
    for dist in fixtures_dir.glob("**/dist"):
        if dist.is_dir():
            shutil.rmtree(str(dist))


def test_wheel_module():
    poetry = poetry_for("module1")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.file.parent / "dist" / "module1-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "module1.py" in z.namelist()


def test_wheel_package():
    poetry = poetry_for("complete")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.file.parent / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package/sub_pkg1/__init__.py" in z.namelist()


def test_wheel_prerelease():
    poetry = poetry_for("prerelease")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.file.parent / "dist" / "prerelease-0.1b1-py2.py3-none-any.whl"

    assert whl.exists()


def test_wheel_excluded_data():
    poetry = poetry_for("default_with_excluded_data_toml")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.file.parent / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package/__init__.py" in z.namelist()
        assert "my_package/data/sub_data/data2.txt" in z.namelist()
        assert "my_package/data/sub_data/data3.txt" in z.namelist()
        assert "my_package/data/data1.txt" not in z.namelist()


def test_wheel_excluded_nested_data():
    poetry = poetry_for("exclude_nested_data_toml")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.file.parent / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package/__init__.py" in z.namelist()
        assert "my_package/data/sub_data/data2.txt" not in z.namelist()
        assert "my_package/data/sub_data/data3.txt" not in z.namelist()
        assert "my_package/data/data1.txt" not in z.namelist()
        assert "my_package/data/data2.txt" in z.namelist()
        assert "my_package/puplic/publicdata.txt" in z.namelist()
        assert "my_package/public/item1/itemdata1.txt" not in z.namelist()
        assert "my_package/public/item1/subitem/subitemdata.txt" not in z.namelist()
        assert "my_package/public/item2/itemdata2.txt" not in z.namelist()


def test_wheel_localversionlabel():
    poetry = poetry_for("localversionlabel")
    WheelBuilder.make(poetry, NullEnv(), NullIO())
    local_version_string = "localversionlabel-0.1b1+gitbranch.buildno.1"
    whl = poetry.file.parent / "dist" / (local_version_string + "-py2.py3-none-any.whl")

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert local_version_string + ".dist-info/METADATA" in z.namelist()

    uploader = Uploader(poetry, NullIO())
    assert whl in uploader.files


def test_wheel_package_src():
    poetry = poetry_for("source_package")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.file.parent / "dist" / "package_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "package_src/__init__.py" in z.namelist()
        assert "package_src/module.py" in z.namelist()


def test_wheel_module_src():
    poetry = poetry_for("source_file")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.file.parent / "dist" / "module_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "module_src.py" in z.namelist()


def test_dist_info_file_permissions():
    poetry = poetry_for("complete")
    WheelBuilder.make(poetry_for("complete"), NullEnv(), NullIO())

    whl = poetry.file.parent / "dist" / "my_package-1.2.3-py3-none-any.whl"

    with zipfile.ZipFile(str(whl)) as z:
        assert (
            z.getinfo("my_package-1.2.3.dist-info/WHEEL").external_attr == 0o644 << 16
        )
        assert (
            z.getinfo("my_package-1.2.3.dist-info/METADATA").external_attr
            == 0o644 << 16
        )
        assert (
            z.getinfo("my_package-1.2.3.dist-info/RECORD").external_attr == 0o644 << 16
        )
        assert (
            z.getinfo("my_package-1.2.3.dist-info/entry_points.txt").external_attr
            == 0o644 << 16
        )

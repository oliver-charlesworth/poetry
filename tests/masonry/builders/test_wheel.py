# -*- coding: utf-8 -*-
import zipfile

from clikit.io import NullIO

from poetry.masonry.builders.wheel import WheelBuilder
from poetry.masonry.publishing.uploader import Uploader
from tests.mock_envs import NullEnv


def test_wheel_module(poetry_factory):
    poetry = poetry_factory("module1")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.root / "dist" / "module1-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "module1.py" in z.namelist()


def test_wheel_package(poetry_factory):
    poetry = poetry_factory("complete")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.root / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package/sub_pkg1/__init__.py" in z.namelist()


def test_wheel_prerelease(poetry_factory):
    poetry = poetry_factory("prerelease")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.root / "dist" / "prerelease-0.1b1-py2.py3-none-any.whl"

    assert whl.exists()


def test_wheel_excluded_data(poetry_factory):
    poetry = poetry_factory("default_with_excluded_data_toml")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.root / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "my_package/__init__.py" in z.namelist()
        assert "my_package/data/sub_data/data2.txt" in z.namelist()
        assert "my_package/data/sub_data/data3.txt" in z.namelist()
        assert "my_package/data/data1.txt" not in z.namelist()


def test_wheel_excluded_nested_data(poetry_factory):
    poetry = poetry_factory("exclude_nested_data_toml")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.root / "dist" / "my_package-1.2.3-py3-none-any.whl"

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


def test_wheel_localversionlabel(poetry_factory):
    poetry = poetry_factory("localversionlabel")
    WheelBuilder.make(poetry, NullEnv(), NullIO())
    local_version_string = "localversionlabel-0.1b1+gitbranch.buildno.1"
    whl = poetry.root / "dist" / (local_version_string + "-py2.py3-none-any.whl")

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert local_version_string + ".dist-info/METADATA" in z.namelist()

    uploader = Uploader(poetry, NullIO())
    assert whl in uploader.files


def test_wheel_package_src(poetry_factory):
    poetry = poetry_factory("source_package")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.root / "dist" / "package_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "package_src/__init__.py" in z.namelist()
        assert "package_src/module.py" in z.namelist()


def test_wheel_module_src(poetry_factory):
    poetry = poetry_factory("source_file")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.root / "dist" / "module_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        assert "module_src.py" in z.namelist()


def test_dist_info_file_permissions(poetry_factory):
    poetry = poetry_factory("complete")
    WheelBuilder.make(poetry, NullEnv(), NullIO())

    whl = poetry.root / "dist" / "my_package-1.2.3-py3-none-any.whl"

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

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import ast
import os
import re
import sys
import tarfile
import zipfile

import pytest

from clikit.io import NullIO

from poetry import __version__
from poetry.masonry.builders import CompleteBuilder
from poetry.utils._compat import decode
from tests.mock_envs import NullEnv


@pytest.mark.skipif(
    sys.platform == "win32" and sys.version_info <= (3, 6),
    reason="Disable test on Windows for Python <=3.6",
)
def test_wheel_c_extension(poetry_factory):
    poetry = poetry_factory("extended")
    builder = CompleteBuilder(poetry, NullEnv(execute=True), NullIO())
    builder.build()

    sdist = poetry.root / "dist" / "extended-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "extended-0.1/build.py" in tar.getnames()
        assert "extended-0.1/extended/extended.c" in tar.getnames()

    whl = list((poetry.root / "dist").glob("extended-0.1-cp*-cp*-*.whl"))[0]

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    has_compiled_extension = False
    for name in zip.namelist():
        if name.startswith("extended/extended") and name.endswith((".so", ".pyd")):
            has_compiled_extension = True

    assert has_compiled_extension

    try:
        wheel_data = decode(zip.read("extended-0.1.dist-info/WHEEL"))

        assert (
            re.match(
                """(?m)^\
Wheel-Version: 1.0
Generator: poetry {}
Root-Is-Purelib: false
Tag: cp[23]\\d-cp[23]\\dm?u?-.+
$""".format(
                    __version__
                ),
                wheel_data,
            )
            is not None
        )

        records = decode(zip.read("extended-0.1.dist-info/RECORD"))

        assert re.search(r"\s+extended/extended.*\.(so|pyd)", records) is not None
    finally:
        zip.close()


@pytest.mark.skipif(
    sys.platform == "win32" and sys.version_info <= (3, 6),
    reason="Disable test on Windows for Python <=3.6",
)
def test_wheel_c_extension_src_layout(poetry_factory):
    poetry = poetry_factory("src_extended")
    builder = CompleteBuilder(poetry, NullEnv(execute=True), NullIO())
    builder.build()

    sdist = poetry.root / "dist" / "extended-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "extended-0.1/build.py" in tar.getnames()
        assert "extended-0.1/src/extended/extended.c" in tar.getnames()

    whl = list((poetry.root / "dist").glob("extended-0.1-cp*-cp*-*.whl"))[0]

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    has_compiled_extension = False
    for name in zip.namelist():
        if name.startswith("extended/extended") and name.endswith((".so", ".pyd")):
            has_compiled_extension = True

    assert has_compiled_extension

    try:
        wheel_data = decode(zip.read("extended-0.1.dist-info/WHEEL"))

        assert (
            re.match(
                """(?m)^\
Wheel-Version: 1.0
Generator: poetry {}
Root-Is-Purelib: false
Tag: cp[23]\\d-cp[23]\\dm?u?-.+
$""".format(
                    __version__
                ),
                wheel_data,
            )
            is not None
        )

        records = decode(zip.read("extended-0.1.dist-info/RECORD"))

        assert re.search(r"\s+extended/extended.*\.(so|pyd)", records) is not None
    finally:
        zip.close()


def test_complete(poetry_factory):
    poetry = poetry_factory("complete")
    builder = CompleteBuilder(poetry, NullEnv(execute=True), NullIO())
    builder.build()

    whl = poetry.root / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()
    if sys.platform != "win32":
        assert (os.stat(str(whl)).st_mode & 0o777) == 0o644

    zip = zipfile.ZipFile(str(whl))

    try:
        assert "my_package/sub_pgk1/extra_file.xml" not in zip.namelist()

        entry_points = zip.read("my_package-1.2.3.dist-info/entry_points.txt")

        assert (
            decode(entry_points.decode())
            == """\
[console_scripts]
extra-script=my_package.extra:main[time]
my-2nd-script=my_package:main2
my-script=my_package:main

"""
        )
        wheel_data = decode(zip.read("my_package-1.2.3.dist-info/WHEEL"))

        assert (
            wheel_data
            == """\
Wheel-Version: 1.0
Generator: poetry {}
Root-Is-Purelib: true
Tag: py3-none-any
""".format(
                __version__
            )
        )
        wheel_data = decode(zip.read("my_package-1.2.3.dist-info/METADATA"))

        assert (
            wheel_data
            == """\
Metadata-Version: 2.1
Name: my-package
Version: 1.2.3
Summary: Some description.
Home-page: https://python-poetry.org/
License: MIT
Keywords: packaging,dependency,poetry
Author: Sébastien Eustace
Author-email: sebastien@eustace.io
Maintainer: People Everywhere
Maintainer-email: people@everywhere.com
Requires-Python: >=3.6,<4.0
Classifier: License :: OSI Approved :: MIT License
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python :: 3.6
Classifier: Programming Language :: Python :: 3.7
Classifier: Programming Language :: Python :: 3.8
Classifier: Topic :: Software Development :: Build Tools
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Provides-Extra: time
Requires-Dist: cachy[msgpack] (>=0.2.0,<0.3.0)
Requires-Dist: cleo (>=0.6,<0.7)
Requires-Dist: pendulum (>=1.4,<2.0); (python_version ~= "2.7" and sys_platform == "win32" or python_version in "3.4 3.5") and (extra == "time")
Project-URL: Documentation, https://python-poetry.org/docs
Project-URL: Issue Tracker, https://github.com/python-poetry/poetry/issues
Project-URL: Repository, https://github.com/python-poetry/poetry
Description-Content-Type: text/x-rst

My Package
==========

"""
        )
    finally:
        zip.close()


def test_complete_no_vcs(poetry_factory):
    poetry = poetry_factory("complete")
    builder = CompleteBuilder(poetry, NullEnv(execute=True), NullIO())
    builder.build()

    whl = poetry.root / "dist" / "my_package-1.2.3-py3-none-any.whl"

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    # Check the zipped file to be sure that included and excluded files are
    # correctly taken account of without vcs
    expected_name_list = [
        "my_package/__init__.py",
        "my_package/data1/test.json",
        "my_package/sub_pkg1/__init__.py",
        "my_package/sub_pkg2/__init__.py",
        "my_package/sub_pkg2/data2/data.json",
        "my_package-1.2.3.dist-info/entry_points.txt",
        "my_package-1.2.3.dist-info/LICENSE",
        "my_package-1.2.3.dist-info/WHEEL",
        "my_package-1.2.3.dist-info/METADATA",
        "my_package-1.2.3.dist-info/RECORD",
    ]

    assert sorted(zip.namelist()) == sorted(expected_name_list)

    try:
        entry_points = zip.read("my_package-1.2.3.dist-info/entry_points.txt")

        assert (
            decode(entry_points.decode())
            == """\
[console_scripts]
extra-script=my_package.extra:main[time]
my-2nd-script=my_package:main2
my-script=my_package:main

"""
        )
        wheel_data = decode(zip.read("my_package-1.2.3.dist-info/WHEEL"))

        assert (
            wheel_data
            == """\
Wheel-Version: 1.0
Generator: poetry {}
Root-Is-Purelib: true
Tag: py3-none-any
""".format(
                __version__
            )
        )
        wheel_data = decode(zip.read("my_package-1.2.3.dist-info/METADATA"))

        assert (
            wheel_data
            == """\
Metadata-Version: 2.1
Name: my-package
Version: 1.2.3
Summary: Some description.
Home-page: https://python-poetry.org/
License: MIT
Keywords: packaging,dependency,poetry
Author: Sébastien Eustace
Author-email: sebastien@eustace.io
Maintainer: People Everywhere
Maintainer-email: people@everywhere.com
Requires-Python: >=3.6,<4.0
Classifier: License :: OSI Approved :: MIT License
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python :: 3.6
Classifier: Programming Language :: Python :: 3.7
Classifier: Programming Language :: Python :: 3.8
Classifier: Topic :: Software Development :: Build Tools
Classifier: Topic :: Software Development :: Libraries :: Python Modules
Provides-Extra: time
Requires-Dist: cachy[msgpack] (>=0.2.0,<0.3.0)
Requires-Dist: cleo (>=0.6,<0.7)
Requires-Dist: pendulum (>=1.4,<2.0); (python_version ~= "2.7" and sys_platform == "win32" or python_version in "3.4 3.5") and (extra == "time")
Project-URL: Documentation, https://python-poetry.org/docs
Project-URL: Issue Tracker, https://github.com/python-poetry/poetry/issues
Project-URL: Repository, https://github.com/python-poetry/poetry
Description-Content-Type: text/x-rst

My Package
==========

"""
        )
    finally:
        zip.close()


def test_module_src(poetry_factory):
    poetry = poetry_factory("source_file")
    builder = CompleteBuilder(poetry, NullEnv(execute=True), NullIO())
    builder.build()

    sdist = poetry.root / "dist" / "module-src-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "module-src-0.1/src/module_src.py" in tar.getnames()

    whl = poetry.root / "dist" / "module_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    try:
        assert "module_src.py" in zip.namelist()
    finally:
        zip.close()


def test_package_src(poetry_factory):
    poetry = poetry_factory("source_package")
    builder = CompleteBuilder(poetry, NullEnv(execute=True), NullIO())
    builder.build()

    sdist = poetry.root / "dist" / "package-src-0.1.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        assert "package-src-0.1/src/package_src/module.py" in tar.getnames()

    whl = poetry.root / "dist" / "package_src-0.1-py2.py3-none-any.whl"

    assert whl.exists()

    zip = zipfile.ZipFile(str(whl))

    try:
        assert "package_src/__init__.py" in zip.namelist()
        assert "package_src/module.py" in zip.namelist()
    finally:
        zip.close()


def test_package_with_include(poetry_factory):
    poetry = poetry_factory("with-include")

    builder = CompleteBuilder(poetry, NullEnv(), NullIO())
    builder.build()

    sdist = poetry.root / "dist" / "with-include-1.2.3.tar.gz"

    assert sdist.exists()

    with tarfile.open(str(sdist), "r") as tar:
        names = tar.getnames()
        assert len(names) == len(set(names))
        assert "with-include-1.2.3/LICENSE" in names
        assert "with-include-1.2.3/README.rst" in names
        assert "with-include-1.2.3/extra_dir/__init__.py" in names
        assert "with-include-1.2.3/extra_dir/vcs_excluded.txt" in names
        assert "with-include-1.2.3/extra_dir/sub_pkg/__init__.py" in names
        assert "with-include-1.2.3/extra_dir/sub_pkg/vcs_excluded.txt" not in names
        assert "with-include-1.2.3/my_module.py" in names
        assert "with-include-1.2.3/notes.txt" in names
        assert "with-include-1.2.3/package_with_include/__init__.py" in names
        assert "with-include-1.2.3/tests/__init__.py" in names
        assert "with-include-1.2.3/pyproject.toml" in names
        assert "with-include-1.2.3/setup.py" in names
        assert "with-include-1.2.3/PKG-INFO" in names
        assert "with-include-1.2.3/for_wheel_only/__init__.py" not in names
        assert "with-include-1.2.3/src/src_package/__init__.py" in names

        setup = tar.extractfile("with-include-1.2.3/setup.py").read()
        setup_ast = ast.parse(setup)

        setup_ast.body = [n for n in setup_ast.body if isinstance(n, ast.Assign)]
        ns = {}
        exec(compile(setup_ast, filename="setup.py", mode="exec"), ns)
        assert ns["package_dir"] == {"": "src"}
        assert ns["packages"] == [
            "extra_dir",
            "extra_dir.sub_pkg",
            "package_with_include",
            "src_package",
            "tests",
        ]
        assert ns["package_data"] == {"": ["*"]}
        assert ns["modules"] == ["my_module"]

    whl = poetry.root / "dist" / "with_include-1.2.3-py3-none-any.whl"

    assert whl.exists()

    with zipfile.ZipFile(str(whl)) as z:
        names = z.namelist()
        assert len(names) == len(set(names))
        assert "with_include-1.2.3.dist-info/LICENSE" in names
        assert "extra_dir/__init__.py" in names
        assert "extra_dir/vcs_excluded.txt" in names
        assert "extra_dir/sub_pkg/__init__.py" in names
        assert "extra_dir/sub_pkg/vcs_excluded.txt" not in names
        assert "for_wheel_only/__init__.py" in names
        assert "my_module.py" in names
        assert "notes.txt" in names
        assert "package_with_include/__init__.py" in names
        assert "tests/__init__.py" not in names
        assert "src_package/__init__.py" in names

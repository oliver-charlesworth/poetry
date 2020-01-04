import pytest

from cleo import CommandTester

from poetry.console.commands import VersionCommand


@pytest.mark.parametrize(
    "version, rule, expected",
    [
        ("0.0.0", "patch", "0.0.1"),
        ("0.0.0", "minor", "0.1.0"),
        ("0.0.0", "major", "1.0.0"),
        ("0.0", "major", "1.0"),
        ("0.0", "minor", "0.1"),
        ("0.0", "patch", "0.0.1"),
        ("1.2.3", "patch", "1.2.4"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "major", "2.0.0"),
        ("1.2.3", "prepatch", "1.2.4-alpha.0"),
        ("1.2.3", "preminor", "1.3.0-alpha.0"),
        ("1.2.3", "premajor", "2.0.0-alpha.0"),
        ("1.2.3-beta.1", "patch", "1.2.3"),
        ("1.2.3-beta.1", "minor", "1.3.0"),
        ("1.2.3-beta.1", "major", "2.0.0"),
        ("1.2.3-beta.1", "prerelease", "1.2.3-beta.2"),
        ("1.2.3-beta1", "prerelease", "1.2.3-beta.2"),
        ("1.2.3beta1", "prerelease", "1.2.3-beta.2"),
        ("1.2.3b1", "prerelease", "1.2.3-beta.2"),
        ("1.2.3", "prerelease", "1.2.4-alpha.0"),
        ("0.0.0", "1.2.3", "1.2.3"),
    ],
)
def test_increment_version(version, rule, expected):
    assert expected == VersionCommand().increment_version(version, rule).text


def test_version_show(app_factory):
    command = app_factory().find("version")
    tester = CommandTester(command)
    tester.execute()
    assert "simple-project 1.2.3\n" == tester.io.fetch_output()

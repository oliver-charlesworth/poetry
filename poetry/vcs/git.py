# -*- coding: utf-8 -*-
import re
import subprocess

from collections import namedtuple

from poetry.utils._compat import decode


PATTERNS = [
    re.compile(
        r"(git\+)?"
        r"((?P<protocol>\w+)://)"
        r"((?P<user>\w+)@)?"
        r"(?P<resource>[\w.\-]+)"
        r"(:(?P<port>\d+))?"
        r"(?P<pathname>(/(?P<owner>\w+)/)"
        r"((?P<projects>([\w\-/]+)/)?(?P<name>[\w\-]+)(\.git|/)?)?)"
        r"([@#](?P<rev>[^@#]+))?"
        r"$"
    ),
    re.compile(
        r"^(git\+)?"
        r"(?P<protocol>https?|git|ssh|rsync|file)://"
        r"(?:(?P<user>.+)@)*"
        r"(?P<resource>[a-z0-9_.-]*)"
        r"(:?P<port>[\d]+)?"
        r"(?P<pathname>[:/]((?P<owner>[\w\-]+)/(?P<projects>([\w\-/]+)/)?)?"
        r"((?P<name>[\w\-.]+?)(\.git|/)?)?)"
        r"([@#](?P<rev>[^@#]+))?"
        r"$"
    ),
    re.compile(
        r"^(?:(?P<user>.+)@)*"
        r"(?P<resource>[a-z0-9_.-]*)[:]*"
        r"(?P<port>[\d]+)?"
        r"(?P<pathname>/?(?P<owner>.+)/(?P<projects>([\w\-/]+)/)?(?P<name>.+).git)"
        r"([@#](?P<rev>[^@#]+))?"
        r"$"
    ),
    re.compile(
        r"((?P<user>\w+)@)?"
        r"(?P<resource>[\w.\-]+)"
        r"[:/]{1,2}"
        r"(?P<pathname>((?P<owner>\w+)/)?"
        r"(?P<projects>([\w\-/]+)/)?"
        r"((?P<name>[\w\-]+)(\.git|/)?)?)"
        r"([@#](?P<rev>[^@#]+))?"
        r"$"
    ),
]


class ParsedUrl:
    def __init__(self, protocol, resource, pathname, user, port, name, rev):
        self.protocol = protocol
        self.resource = resource
        self.pathname = pathname
        self.user = user
        self.port = port
        self.name = name
        self.rev = rev

    @classmethod
    def parse(cls, url):  # type: () -> ParsedUrl
        for pattern in PATTERNS:
            m = pattern.match(url)
            if m:
                groups = m.groupdict()
                return ParsedUrl(
                    groups.get("protocol"),
                    groups.get("resource"),
                    groups.get("pathname"),
                    groups.get("user"),
                    groups.get("port"),
                    groups.get("name"),
                    groups.get("rev"),
                )

        raise ValueError('Invalid git url "{}"'.format(url))

    @property
    def url(self):  # type: () -> str
        return "{}{}{}{}{}".format(
            "{}://".format(self.protocol) if self.protocol else "",
            "{}@".format(self.user) if self.user else "",
            self.resource,
            ":{}".format(self.port) if self.port else "",
            "/" + self.pathname if self.pathname.startswith(":") else self.pathname,
        )

    def format(self):
        return "{}".format(self.url, "#{}".format(self.rev) if self.rev else "",)

    def __str__(self):  # type: () -> str
        return self.format()


GitUrl = namedtuple("GitUrl", ["url", "revision"])


class GitConfig:
    def __init__(self, work_dir, requires_git_presence=False):
        self._config = {}

        try:
            config_list = decode(
                subprocess.check_output(
                    ["git", "config", "-l"], stderr=subprocess.STDOUT, env=XXX, cwd=work_dir
                )
            )

            m = re.findall("(?ms)^([^=]+)=(.*?)$", config_list)
            if m:
                for group in m:
                    self._config[group[0]] = group[1]
        except (subprocess.CalledProcessError, OSError):
            if requires_git_presence:
                raise

    def get(self, key, default=None):
        return self._config.get(key, default)

    def __getitem__(self, item):
        return self._config[item]


class Git:
    def __init__(self, work_dir):
        self._config = GitConfig(work_dir=work_dir, requires_git_presence=True)
        self._work_dir = work_dir

    @classmethod
    def normalize_url(cls, url):  # type: (str) -> GitUrl
        parsed = ParsedUrl.parse(url)

        formatted = re.sub(r"^git\+", "", url)
        if parsed.rev:
            formatted = re.sub(r"[#@]{}$".format(parsed.rev), "", formatted)

        altered = parsed.format() != formatted

        if altered:
            if re.match(r"^git\+https?", url) and re.match(
                r"^/?:[^0-9]", parsed.pathname
            ):
                normalized = re.sub(r"git\+(.*:[^:]+):(.*)", "\\1/\\2", url)
            elif re.match(r"^git\+file", url):
                normalized = re.sub(r"git\+", "", url)
            else:
                normalized = re.sub(r"^(?:git\+)?ssh://", "", url)
        else:
            normalized = parsed.format()

        return GitUrl(re.sub(r"#[^#]*$", "", normalized), parsed.rev)

    @property
    def config(self):  # type: () -> GitConfig
        return self._config

    def clone(self, repository):  # type: (...) -> str
        return self._run("clone", repository, self._work_dir)

    def checkout(self, rev):  # type: (...) -> str
        return self._run("checkout", rev)

    def rev_parse(self, rev):  # type: (...) -> str
        return self._run("rev-parse", rev)

    def get_ignored_files(self):  # type: (...) -> list
        output = self._run("ls-files", "--others", "-i", "--exclude-standard")

        return output.split("\n")

    def _remote_urls(self):  # type: (...) -> dict
        output = self._run("config", "--get-regexp", r"remote\..*\.url")

        urls = {}
        for url in output.splitlines():
            name, url = url.split(" ", 1)
            urls[name.strip()] = url.strip()

        return urls

    def remote_url(self):  # type: (...) -> str
        urls = self._remote_urls()

        return urls.get("remote.origin.url", urls[list(urls.keys())[0]])

    def _run(self, *args):  # type: (...) -> str
        return decode(
            subprocess.check_output(["git"] + list(args), stderr=subprocess.STDOUT, env=XXX, cwd=self._work_dir)
        ).strip()

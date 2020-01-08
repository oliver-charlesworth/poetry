import os
import sys

from distutils.util import strtobool

from .env_command import EnvCommand


class ShellCommand(EnvCommand):

    name = "shell"
    description = "Spawns a shell within the virtual environment."

    help = """The <info>shell</> command spawns a shell, according to the
<comment>$SHELL</> environment variable, within the virtual environment.
If one doesn't exist yet, it will be created.
"""

    def handle(self):
        from poetry.utils.shell import Shell

        # Check if it's already activated or doesn't exist and won't be created
        venv_activated = strtobool(self.env_vars.get("POETRY_ACTIVE", "0")) or getattr(
            sys, "real_prefix", sys.prefix
        ) == str(self.env.path)
        if venv_activated:
            self.line(
                "Virtual environment already activated: "
                "<info>{}</>".format(self.env.path)
            )

            return

        self.line("Spawning shell within <info>{}</>".format(self.env.path))

        env_vars = dict(self.env_vars)
        env_vars["POETRY_ACTIVE"] = "1"  # Setting this to avoid spawning unnecessary nested shells
        shell = Shell.get()
        shell.activate(self.env, env_vars=env_vars, cwd=self.cwd)

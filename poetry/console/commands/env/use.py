from cleo import argument

from ..command import Command


class EnvUseCommand(Command):

    name = "use"
    description = "Activates or creates a new virtualenv for the current project."

    arguments = [argument("python", "The python executable to use.")]

    def handle(self):
        from poetry.utils.env import EnvManager

        manager = EnvManager(self.poetry, self._io)

        if self.argument("python") == "system":
            manager.deactivate()

            return

        env = manager.activate(self.argument("python"))

        self.line("Using virtualenv: <comment>{}</>".format(env.path))

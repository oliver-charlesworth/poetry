from cleo import argument

from ..command import Command


class EnvRemoveCommand(Command):

    name = "remove"
    description = "Removes a specific virtualenv associated with the project."

    arguments = [
        argument("python", "The python executable to remove the virtualenv for.")
    ]

    def handle(self):
        from poetry.utils.env import EnvManager

        manager = EnvManager(self.poetry)
        removed_path = manager.remove(self.argument("python"))

        self.line("Deleted virtualenv: <comment>{}</comment>".format(removed_path))

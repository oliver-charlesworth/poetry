import os

from .application import Application


def main():
    return Application(env=os.environ).run()

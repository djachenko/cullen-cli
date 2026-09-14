import sys

from cullen._cli.ui.console import INDENT, Console, Stage, Task
from cullen._cli.ui.plain import PlainConsole
from cullen._cli.ui.rich import RichConsole

__all__ = ["INDENT", "Console", "Stage", "Task", "make_console"]


def make_console() -> Console:
    if sys.stdout.isatty():
        return RichConsole()
    else:
        return PlainConsole()

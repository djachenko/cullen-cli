from collections.abc import Iterator
from contextlib import contextmanager

from cullen._cli.ui.console import INDENT, Console, Stage, Task


class PlainTask(Task):
    def describe(self, description: str) -> None:
        print(description)

    def advance(self) -> None:
        pass


class PlainStage(Stage):
    DEPTH = 2

    def __init__(self) -> None:
        self.__shown: list[str] = []

    def tree(self, lines: list[str]) -> None:
        for depth, line in enumerate(lines[:self.DEPTH], start=1):
            if lines[:depth] != self.__shown[:depth]:
                print(f"{INDENT * depth}{line}")

        self.__shown = lines[:self.DEPTH]

    def line(self, text: str, style: str | None = None) -> None:
        print(f"{INDENT}{text}")


class PlainConsole(Console):
    def line(self, text: str, style: str | None = None) -> None:
        print(text)

    @contextmanager
    def stage(self, header: str) -> Iterator[Stage]:
        print(header)

        yield PlainStage()

    def summary(self, rows: list[tuple[str, str]]) -> None:
        width = max((len(label) for label, _ in rows), default=0)

        for label, value in rows:
            print(f"{label.ljust(width)}  {value}")

    @contextmanager
    def progress(self, description: str, total: int | None = None) -> Iterator[Task]:
        print(description)

        yield PlainTask()

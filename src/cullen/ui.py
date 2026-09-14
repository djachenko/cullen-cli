import sys
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager

from rich import console as rich_console
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn
from rich.table import Table


class Task(ABC):
    @abstractmethod
    def describe(self, description: str) -> None:
        pass

    @abstractmethod
    def advance(self) -> None:
        pass


class Console(ABC):
    @abstractmethod
    def line(self, text: str, style: str | None = None) -> None:
        pass

    @abstractmethod
    def summary(self, rows: list[tuple[str, str]]) -> None:
        pass

    @abstractmethod
    def progress(self, description: str, total: int | None = None) -> AbstractContextManager[Task]:
        pass


class PlainTask(Task):
    def describe(self, description: str) -> None:
        print(description)

    def advance(self) -> None:
        pass


class PlainConsole(Console):
    def line(self, text: str, style: str | None = None) -> None:
        print(text)

    def summary(self, rows: list[tuple[str, str]]) -> None:
        width = max((len(label) for label, _ in rows), default=0)

        for label, value in rows:
            print(f"{label.ljust(width)}  {value}")

    @contextmanager
    def progress(self, description: str, total: int | None = None) -> Iterator[Task]:
        print(description)

        yield PlainTask()


class RichTask(Task):
    def __init__(self, progress: Progress, task: TaskID) -> None:
        self.__progress = progress
        self.__task = task

    def describe(self, description: str) -> None:
        self.__progress.update(self.__task, description=description)

    def advance(self) -> None:
        self.__progress.advance(self.__task)


class RichConsole(Console):
    def __init__(self) -> None:
        self.__console = rich_console.Console()

    def line(self, text: str, style: str | None = None) -> None:
        self.__console.print(text, style=style)

    def summary(self, rows: list[tuple[str, str]]) -> None:
        table = Table(show_header=False, box=None)

        table.add_column(style="dim")
        table.add_column(justify="right", style="bold")

        for label, value in rows:
            table.add_row(label, value)

        self.__console.print(table)

    @contextmanager
    def progress(self, description: str, total: int | None = None) -> Iterator[Task]:
        if total is None:
            count_column = TextColumn("[cyan]{task.completed}[/] done")
        else:
            count_column = TextColumn("[cyan]{task.completed}[/] of [cyan]{task.total}[/]")

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                count_column,
                TimeElapsedColumn(),
                console=self.__console,
                transient=True,
        ) as progress:
            yield RichTask(progress, progress.add_task(description, total=total))


def make_console() -> Console:
    if sys.stdout.isatty():
        return RichConsole()

    return PlainConsole()

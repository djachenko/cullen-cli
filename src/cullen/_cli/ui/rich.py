from collections.abc import Iterator
from contextlib import contextmanager

from rich import console as rich_console
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from cullen._cli.ui.console import INDENT, Console, Stage, Task


class RichTask(Task):
    def __init__(self, progress: Progress, task: TaskID) -> None:
        self.__progress = progress
        self.__task = task

    def describe(self, description: str) -> None:
        self.__progress.update(self.__task, description=description)

    def advance(self) -> None:
        self.__progress.advance(self.__task)


class RichStage(Stage):
    def __init__(self, console: rich_console.Console, live: Live) -> None:
        self.__console = console
        self.__live = live

    def tree(self, lines: list[str]) -> None:
        text = Text(style="dim")

        for depth, line in enumerate(lines, start=1):
            text.append(f"{INDENT * depth}{line}\n")

        self.__live.update(text)

    def line(self, text: str, style: str | None = None) -> None:
        self.__console.print(f"{INDENT}{text}", style=style)


class RichConsole(Console):
    def __init__(self) -> None:
        self.__console = rich_console.Console(highlight=False)

    def line(self, text: str, style: str | None = None) -> None:
        self.__console.print(text, style=style)

    @contextmanager
    def stage(self, header: str) -> Iterator[Stage]:
        self.__console.print(header, style="bold")

        with Live(console=self.__console, transient=True) as live:
            yield RichStage(self.__console, live)

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

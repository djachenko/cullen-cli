from contextlib import AbstractContextManager
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Annotated

from justin_utils.util import bfs
from typer import Argument, Option, Typer

from cullen.decisions_file import load
from cullen.errors import DecisionsFileMissingError
from cullen.service_folders import SERVICE_FOLDERS
from cullen.ui import Console, Task, make_console

app = Typer()


@app.command()
def cull(
        paths: Annotated[list[Path] | None, Argument()] = None,
        file: Annotated[Path, Option()] = Path("culled.json"),
) -> None:
    if paths is None:
        paths = [Path(".")]

    output = CullOutput(make_console())

    reports: list[Report] = []

    for path in sorted(paths):
        try:
            decisions_file = load(path / file)
        except DecisionsFileMissingError as error:
            output.skipped(path.name, error)

            continue

        categories = set(decisions_file.decisions)

        reverse_mapping = {
            stem: category
            for category, stems in decisions_file.decisions.items()
            for stem in stems
        }

        with output.culling(path.name) as task:
            report = Report(task)

            bfs(path, partial(_handle_folder, categories=categories, reverse_mapping=reverse_mapping, report=report))

        output.culled(path.name, report)

        reports.append(report)

    output.summarize(reports)


@dataclass
class Report:
    task: Task
    folders: int = 0
    moved_up: int = 0
    moved_down: int = 0

    def visit(self, path: Path) -> None:
        self.folders += 1

        self.task.describe(path.name)

    def up(self) -> None:
        self.moved_up += 1

        self.task.advance()

    def down(self) -> None:
        self.moved_down += 1

        self.task.advance()


class CullOutput:
    def __init__(self, console: Console) -> None:
        self.__console = console

    def culling(self, description: str) -> AbstractContextManager[Task]:
        return self.__console.progress(description)

    def skipped(self, name: str, error: DecisionsFileMissingError) -> None:
        self.__console.line(f"{name}: {error}, skipped", style="yellow")

    def culled(self, name: str, report: Report) -> None:
        self.__console.line(f"{name}: {report.moved_up} up, {report.moved_down} down")

    def summarize(self, reports: list[Report]) -> None:
        self.__console.summary([
            ("sets", str(len(reports))),
            ("folders", str(sum(report.folders for report in reports))),
            ("moved up", str(sum(report.moved_up for report in reports))),
            ("moved down", str(sum(report.moved_down for report in reports))),
        ])


def _handle_folder(
        path: Path,
        categories: set[str],
        reverse_mapping: dict[str, str],
        report: Report,
) -> list[Path]:
    if path.name in SERVICE_FOLDERS:
        return []

    report.visit(path)

    _flatten(path, categories, report)
    _distribute(path, reverse_mapping, report)

    return [item for item in path.iterdir() if item.is_dir() and item.name not in categories]


def _flatten(path: Path, categories: set[str], report: Report) -> None:
    for category in categories:
        category_path = path / category

        if not category_path.is_dir():
            continue

        for item in list(category_path.iterdir()):
            new_path = path / item.name

            item.rename(new_path)

            report.up()


def _distribute(path: Path, reverse_mapping: dict[str, str], report: Report) -> None:
    for item in list(path.iterdir()):
        if not item.is_file():
            continue

        category = reverse_mapping.get(item.stem)

        if category is None:
            continue

        category_path = path / category
        category_path.mkdir(parents=True, exist_ok=True)

        new_path = category_path / item.name

        item.rename(new_path)

        report.down()


if __name__ == '__main__':
    app("/Users/justin/photos/stages/stage1.filter/26.03.22.fen_init_lab".split())

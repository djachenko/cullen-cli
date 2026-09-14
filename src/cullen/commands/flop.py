from contextlib import AbstractContextManager
from pathlib import Path
from typing import Annotated

from typer import Argument, Option, Typer

from cullen.decisions_file import load
from cullen.errors import FlopError
from cullen.service_folders import SERVICE_FOLDERS
from cullen.ui import Console, Task, make_console

app = Typer()


class FlopOutput:
    def __init__(self, console: Console) -> None:
        self.__console = console

    def planned(self, source: Path, destination: Path) -> None:
        self.__console.line(f"{source} → {destination}")

    def moving(self, description: str, total: int) -> AbstractContextManager[Task]:
        return self.__console.progress(description, total)

    def summarize(self, files: int, moves: int, *, dry_run: bool) -> None:
        if dry_run:
            moves_label = "to move"
        else:
            moves_label = "moved"

        self.__console.summary([
            ("files", str(files)),
            (moves_label, str(moves)),
        ])


@app.command()
def flop(
        path: Annotated[Path, Argument(resolve_path=True)] = Path(".."),
        file: Annotated[Path, Argument()] = Path("culled.json"),
        dry_run: Annotated[bool, Option("--dry-run")] = False,
) -> None:
    categories = set(load(path / file).decisions)

    files = sorted(item for item in path.rglob("*") if item.is_file())
    moves = _plan(files, path, categories)

    output = FlopOutput(make_console())

    if dry_run:
        for source, destination in moves:
            output.planned(source.relative_to(path), destination.relative_to(path))
    else:
        _move(moves, path, output)

    output.summarize(len(files), len(moves), dry_run=dry_run)


def _plan(files: list[Path], path: Path, categories: set[str]) -> list[tuple[Path, Path]]:
    moves = []
    sources: dict[Path, Path] = {}

    for item in files:
        relative_path = item.relative_to(path)
        relative_parts = list(relative_path.parent.parts)

        if any(part in SERVICE_FOLDERS for part in relative_parts):
            continue

        found = [part for part in relative_parts if part in categories]

        if not found:
            continue

        if len(found) > 1:
            raise FlopError(f"multiple categories in path: {relative_path}")

        category = found[0]

        relative_parts.remove(category)

        destination = path.joinpath(category, *relative_parts, item.name)
        relative_destination = destination.relative_to(path)

        if relative_destination in sources:
            raise FlopError(
                f"{sources[relative_destination]} and {relative_path} both land on {relative_destination}",
            )

        sources[relative_destination] = relative_path

        moves.append((item, destination))

    return moves


def _move(moves: list[tuple[Path, Path]], path: Path, output: FlopOutput) -> None:
    with output.moving(path.name or str(path), len(moves)) as task:
        for source, destination in moves:
            destination.parent.mkdir(parents=True, exist_ok=True)

            task.describe(source.name)

            source.rename(destination)

            task.advance()

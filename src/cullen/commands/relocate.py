from contextlib import AbstractContextManager
from pathlib import Path
from typing import Annotated

from justin_utils.dictable import DictableError, frompath
from justin_utils.util import bfs
from typer import Argument, Typer

from cullen.decisions_file import DecisionsFile
from cullen.errors import DecisionsFileError
from cullen.ui import Console, Task, make_console

app = Typer()


class RelocateOutput:
    def __init__(self, console: Console) -> None:
        self.__console = console

    def nothing_to_relocate(self, path: Path) -> None:
        self.__console.line(f"no decisions files in {path}", style="yellow")

    def scanning(self, description: str, total: int) -> AbstractContextManager[Task]:
        return self.__console.progress(description, total)

    def relocated(self, name: str) -> None:
        self.__console.line(f"relocated {name}", style="green")

    def not_found(self, names: list[str]) -> None:
        self.__console.line(f"not found {', '.join(names)}", style="yellow")


@app.command()
def relocate(
        path: Annotated[Path, Argument()],
        root: Annotated[Path, Argument()] = Path("/Volumes"),
) -> None:
    if not path.is_dir():
        raise DecisionsFileError(f"no such folder: {path}")

    if not root.is_dir():
        raise DecisionsFileError(f"no such folder: {root}")

    decisions_files: dict[str, Path] = {}

    for item in path.glob("*.json"):
        try:
            decisions_files[frompath(item, DecisionsFile).name] = item
        except DictableError:
            pass

    output = RelocateOutput(make_console())

    if not decisions_files:
        output.nothing_to_relocate(path)

        return

    relocated: list[str] = []

    with output.scanning(root.name or str(root), len(decisions_files)) as task:
        def provider(folder: Path) -> list[Path]:
            if not decisions_files:
                return []

            task.describe(folder.name or str(folder))

            if folder.name in decisions_files:
                cullen_folder = folder / "cullen"

                if cullen_folder.is_dir():
                    new_path = folder / "culled.json"

                    decisions_files.pop(folder.name).rename(new_path)

                    relocated.append(folder.name)

                    task.advance()

                    return []

            try:
                # симлинки не разворачиваем: /Volumes/Macintosh HD ведёт на /,
                # а внутри снова /Volumes — обход зациклился бы навсегда
                return [item for item in folder.iterdir() if item.is_dir() and not item.is_symlink()]
            except PermissionError:
                return []

        bfs(root, provider)

    for name in relocated:
        output.relocated(name)

    if decisions_files:
        output.not_found(sorted(decisions_files))

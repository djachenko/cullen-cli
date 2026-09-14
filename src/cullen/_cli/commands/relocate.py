from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, ClassVar

from justin_utils.dictable import DictableError, frompath
from justin_utils.util import bfs
from typer import Argument, Option, Typer

from cullen import DecisionsFile, DecisionsFileError
from cullen._cli.ui import Console, Stage, make_console

app = Typer()


class Discovery:
    def __init__(self, stage: Stage) -> None:
        self._stage = stage

    def found(self, file: Path) -> None:
        self._stage.line(f"found {file.name}", style="green")


class Scan:
    def __init__(self, stage: Stage, root: Path) -> None:
        self._stage = stage
        self._root = root

    def visiting(self, folder: Path) -> None:
        self._stage.tree([str(self._root), *folder.relative_to(self._root).parts])


class Relocation:
    def __init__(self, stage: Stage) -> None:
        self._stage = stage

    def relocated(self, file: Path, folder: Path) -> None:
        self._stage.line(f"{file.name} → {folder}", style="green")

    def not_found(self, file: Path, name: str, root: Path) -> None:
        self._stage.line(f'{file.name}: not found photoset "{name}" under {root}', style="yellow")


class RelocateOutput:
    def __init__(self, console: Console) -> None:
        self._console = console

    @contextmanager
    def discovering(self) -> Iterator[Discovery]:
        with self._console.stage("Discovering files:") as stage:
            yield Discovery(stage)

    def nothing_to_relocate(self) -> None:
        self._console.line("nothing to relocate", style="yellow")

    @contextmanager
    def scanning(self, root: Path) -> Iterator[Scan]:
        with self._console.stage("Scanning:") as stage:
            yield Scan(stage, root)

    @contextmanager
    def relocating(self) -> Iterator[Relocation]:
        with self._console.stage("Relocating:") as stage:
            yield Relocation(stage)

    @contextmanager
    def not_relocated(self) -> Iterator[Relocation]:
        with self._console.stage("Not relocated:") as stage:
            yield Relocation(stage)


class Relocator:
    _SYSTEM_FOLDERS: ClassVar[frozenset[Path]] = frozenset({
        Path("/Applications"),
        Path("/Library"),
        Path("/System"),
        Path("/bin"),
        Path("/cores"),
        Path("/dev"),
        Path("/opt"),
        Path("/private"),
        Path("/sbin"),
        Path("/usr"),
    })

    def __init__(self, paths: list[Path], root: Path, output: RelocateOutput) -> None:
        self._paths = paths
        self._root = root
        self._output = output

    def run(self) -> None:
        decisions_files = self._discover_decisions_files()

        if not decisions_files:
            self._output.nothing_to_relocate()

            return

        photosets = self._find_photosets(decisions_files)

        missing = self._relocate_decisions(photosets, decisions_files)

        self._report_missing_photosets(missing)

    def _discover_decisions_files(self) -> dict[str, Path]:
        decisions_files: dict[str, Path] = {}

        with self._output.discovering() as discovery:
            for path in self._paths:
                for item in self._candidates(path):
                    try:
                        decisions_files[frompath(item, DecisionsFile).name] = item
                    except DictableError:
                        continue

                    discovery.found(item)

        return decisions_files

    def _find_photosets(self, decisions_files: dict[str, Path]) -> dict[str, Path]:
        photosets: dict[str, Path] = {}

        with self._output.scanning(self._root) as scan:
            def provider(folder: Path) -> list[Path]:
                if len(photosets) == len(decisions_files):
                    return []

                scan.visiting(folder)

                if folder.name in decisions_files and (folder / "cullen").is_dir():
                    photosets[folder.name] = folder

                    return []

                try:
                    return [item for item in folder.iterdir() if self._walkable(item)]
                except PermissionError:
                    return []

            bfs(self._root, provider)

        return photosets

    def _relocate_decisions(self, photosets: dict[str, Path], decisions_files: dict[str, Path]) -> dict[str, Path]:
        decisions_files = decisions_files.copy()

        if not photosets:
            return decisions_files

        with self._output.relocating() as relocation:
            for name, folder in photosets.items():
                file = decisions_files.pop(name)

                file.rename(folder / "culled.json")

                relocation.relocated(file, folder)

        return decisions_files

    def _report_missing_photosets(self, missing: dict[str, Path]) -> None:
        if not missing:
            return

        with self._output.not_relocated() as relocation:
            for name, file in sorted(missing.items()):
                relocation.not_found(file, name, self._root)

    @staticmethod
    def _candidates(path: Path) -> list[Path]:
        if path.is_dir():
            candidates = [item for item in path.iterdir() if item.is_file()]
        else:
            candidates = [path]

        return [item for item in candidates if Relocator._looks_like_json(item)]

    @staticmethod
    def _looks_like_json(file: Path) -> bool:
        with file.open("rb") as stream:
            return stream.read(1) == b"{"

    @staticmethod
    def _walkable(folder: Path) -> bool:
        # symlinks are not followed: /Volumes/Macintosh HD points to /,
        # which contains /Volumes again, and the walk would never end
        if not folder.is_dir() or folder.is_symlink():
            return False

        return not folder.name.startswith(".") and folder not in Relocator._SYSTEM_FOLDERS


@app.command()
def relocate(
        paths: Annotated[list[Path] | None, Argument()] = None,
        root: Annotated[Path, Option("--root")] = Path("/"),
) -> None:
    paths = paths or [Path(".")]

    for path in paths:
        if not path.exists():
            raise DecisionsFileError(f"no such path: {path}")

    if not root.is_dir():
        raise DecisionsFileError(f"no such folder: {root}")

    Relocator(paths, root, RelocateOutput(make_console())).run()

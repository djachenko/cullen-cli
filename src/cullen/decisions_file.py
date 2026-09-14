from dataclasses import dataclass
from pathlib import Path

from justin_utils.dictable import DictableDataclass, DictableError, frompath

from cullen.errors import DecisionsFileError, DecisionsFileMissingError


@dataclass(frozen=True)
class DecisionsFile(DictableDataclass):
    name: str
    decisions: dict[str, list[str]]


def load(path: Path) -> DecisionsFile:
    if not path.is_file():
        raise DecisionsFileMissingError(f"no decisions file at {path}")

    try:
        return frompath(path, DecisionsFile)
    except DictableError as error:
        raise DecisionsFileError(str(error)) from error

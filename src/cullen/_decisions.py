from dataclasses import dataclass
from pathlib import Path
from typing import Self

from justin_utils.dictable import DictableDataclass, DictableError, frompath

from cullen._errors import CullenDecisionsError, CullenDecisionsMissingError


@dataclass(frozen=True)
class CullenDecisions(DictableDataclass):
    name: str
    decisions: dict[str, list[str]]

    @classmethod
    def load(cls, path: Path) -> Self:
        if not path.is_file():
            raise CullenDecisionsMissingError(f"no decisions file at {path}")

        try:
            return frompath(path, cls)
        except DictableError as error:
            raise CullenDecisionsError(str(error)) from error

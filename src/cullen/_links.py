import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


class CullenPhotosetId:
    @staticmethod
    def make(set_name: str, part_name: str | None = None) -> str:
        if part_name is None:
            return set_name
        else:
            return f"{set_name}.{part_name}"

    @staticmethod
    def candidates(folder: Path) -> Iterable[str]:
        return CullenPhotosetId.make(folder.name), CullenPhotosetId.make(folder.parent.name, folder.name)


@dataclass(frozen=True)
class CullenLinks:
    set_name: str
    part_name: str | None
    links: list[tuple[str, str]]

    @property
    def name(self) -> str:
        return f"{CullenPhotosetId.make(self.set_name, self.part_name)}.json"


    def save(self, folder: Path) -> None:
        entries = [{"name": name, "url": url} for name, url in self.links]

        folder.mkdir(parents=True, exist_ok=True)

        with (folder / self.name).open("w") as file:
            json.dump(entries, file, indent=4)

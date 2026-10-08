import json
from dataclasses import dataclass
from pathlib import Path


def photoset_id(set_name: str, part_name: str | None = None) -> str:
    if part_name is None:
        return set_name

    return f"{set_name}.{part_name}"


@dataclass(frozen=True)
class CullenLinks:
    set_name: str
    part_name: str | None
    links: dict[str, str]

    def save(self, folder: Path) -> None:
        entries = [{"name": name, "url": url} for name, url in self.links.items()]

        with (folder / f"{photoset_id(self.set_name, self.part_name)}.json").open("w") as file:
            json.dump(entries, file, indent=4)

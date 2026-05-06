import json
from pathlib import Path
from typing import Annotated

from typer import Typer, Argument

app = Typer()

@app.command()
def cullen(
        path: Annotated[Path, Argument()] = Path.cwd(),
        file_name: Annotated[str, Argument()] = "cullen.json"
) -> None:
    cullen_file_path = path / file_name

    if not cullen_file_path.exists():
        return

    if not cullen_file_path.is_file():
        return

    with cullen_file_path.open() as cullen_file:
        cullen_data = json.load(cullen_file)

    decisions = cullen_data["decisions"]

    for dest in decisions:
        dest_path = path / dest

        if not dest_path.exists():
            continue

        for item in dest_path.iterdir():
            new_path = path / item.name

            item.rename(new_path)

            print(f"move up {item.relative_to(path)} to {new_path.relative_to(path)}")

    reverse_mapping = {}

    for dest, stems in decisions.items():
        for stem in stems:
            stem = stem.removesuffix(".jpg")

            reverse_mapping[stem] = dest

    for item in path.iterdir():
        if not item.stem in reverse_mapping:
            print(f"Not moving {item.name}")

            continue

        dest_folder_name = reverse_mapping[item.stem]

        dest_path = path / dest_folder_name
        dest_path.mkdir(parents=True, exist_ok=True)

        new_path = dest_path / item.name

        print(f"move down {item.relative_to(path)} to {new_path.relative_to(path)}")

        item.rename(new_path)


if __name__ == '__main__':
    app("/Users/justin/photos/stages/stage1.filter/26.04.17.wolfday".split())



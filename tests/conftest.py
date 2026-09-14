import json
from collections.abc import Callable
from pathlib import Path

import pytest

FileTree = dict[str, "FileTree | str | None"]

Photoset = Callable[[FileTree, dict[str, list[str]]], Path]
Tree = Callable[[Path], set[str]]


@pytest.fixture
def create_files() -> Callable[[Path, FileTree], None]:
    def _create(root: Path, structure: FileTree) -> None:
        for key, value in structure.items():
            new_path = root / key

            if value is None:
                new_path.touch()
            elif isinstance(value, str):
                new_path.write_text(value)
            elif isinstance(value, dict):
                new_path.mkdir(parents=True, exist_ok=True)

                _create(new_path, value)

    return _create


@pytest.fixture
def photoset(tmp_path: Path, create_files: Callable[[Path, FileTree], None]) -> Photoset:
    def _create(structure: FileTree, decisions: dict[str, list[str]]) -> Path:
        root = tmp_path / "photoset"

        root.mkdir(parents=True, exist_ok=True)

        create_files(root, structure)

        (root / "culled.json").write_text(json.dumps({
            "name": root.name,
            "decisions": decisions,
        }))

        return root

    return _create


@pytest.fixture
def tree() -> Tree:
    def _tree(root: Path) -> set[str]:
        return {str(item.relative_to(root)) for item in root.rglob("*") if item.is_file()}

    return _tree

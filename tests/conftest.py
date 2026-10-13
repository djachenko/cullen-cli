import json
from collections.abc import Callable
from pathlib import Path

import pytest
from justin_utils.testing import CreateFiles, FileTree

Photoset = Callable[[FileTree, dict[str, list[str]]], Path]
Tree = Callable[[Path], set[str]]


@pytest.fixture
def photoset(tmp_path: Path, create_files: CreateFiles) -> Photoset:
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
        return {item.relative_to(root).as_posix() for item in root.rglob("*") if item.is_file()}

    return _tree

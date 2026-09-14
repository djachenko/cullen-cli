import json
from collections.abc import Callable
from pathlib import Path

import pytest

from conftest import FileTree

from cullen.errors import DecisionsFileError
from cullen.commands.relocate import relocate


@pytest.fixture
def downloads(tmp_path: Path) -> Path:
    path = tmp_path / "downloads"

    path.mkdir()

    return path


def write_decisions(path: Path, name: str) -> Path:
    path.write_text(json.dumps({"name": name, "decisions": {"good": []}}))

    return path


class TestRelocate:
    def test_missing_downloads_folder_reports(self, tmp_path: Path) -> None:
        stages = tmp_path / "stages"

        stages.mkdir()

        with pytest.raises(DecisionsFileError):
            relocate(tmp_path / "nowhere", stages)

    def test_missing_root_reports(self, downloads: Path, tmp_path: Path) -> None:
        with pytest.raises(DecisionsFileError):
            relocate(downloads, tmp_path / "nowhere")

    def test_empty_downloads_reports(self, capsys, downloads: Path, tmp_path: Path) -> None:
        stages = tmp_path / "stages"

        stages.mkdir()

        relocate(downloads, stages)

        assert "no decisions files" in capsys.readouterr().out

    def test_moves_decisions_file_into_photoset(
            self,
            tmp_path: Path,
            downloads: Path,
            create_files: Callable[[Path, FileTree], None],
    ) -> None:
        stages = tmp_path / "stages"

        create_files(stages, {"stage": {"photoset": {"cullen": {}}}})
        write_decisions(downloads / "culled-1.json", "photoset")

        relocate(downloads, stages)

        assert (stages / "stage/photoset/culled.json").is_file()
        assert not (downloads / "culled-1.json").exists()

    def test_leaves_file_when_photoset_has_no_cullen_folder(
            self,
            tmp_path: Path,
            downloads: Path,
            create_files: Callable[[Path, FileTree], None],
    ) -> None:
        stages = tmp_path / "stages"

        create_files(stages, {"photoset": {}})
        write_decisions(downloads / "culled-1.json", "photoset")

        relocate(downloads, stages)

        assert (downloads / "culled-1.json").is_file()

    def test_binary_json_is_ignored(self, tmp_path: Path, downloads: Path) -> None:
        stages = tmp_path / "stages"

        stages.mkdir()

        (downloads / "._culled.json").write_bytes(b"\x00\x05\x16\x07\x00\x02\x00\x00Mac OS X")

        relocate(downloads, stages)

        assert (downloads / "._culled.json").is_file()

    def test_ignores_non_json_files(self, tmp_path: Path, downloads: Path) -> None:
        stages = tmp_path / "stages"

        stages.mkdir()

        (downloads / "readme.txt").write_text("не json")

        relocate(downloads, stages)

        assert (downloads / "readme.txt").is_file()

    def test_json_without_decisions_is_ignored(
            self,
            tmp_path: Path,
            downloads: Path,
            create_files: Callable[[Path, FileTree], None],
    ) -> None:
        stages = tmp_path / "stages"

        create_files(stages, {"photoset": {"cullen": {}}})
        (downloads / "_meta.json").write_text(json.dumps({"album": "photoset"}))

        relocate(downloads, stages)

        assert (downloads / "_meta.json").is_file()

    def test_does_not_descend_into_matched_photoset(
            self,
            tmp_path: Path,
            downloads: Path,
            create_files: Callable[[Path, FileTree], None],
    ) -> None:
        stages = tmp_path / "stages"

        create_files(stages, {
            "photoset": {
                "cullen": {},
                "inner": {"cullen": {}},
            },
        })
        write_decisions(downloads / "culled-1.json", "photoset")
        write_decisions(downloads / "culled-2.json", "inner")

        relocate(downloads, stages)

        assert (stages / "photoset/culled.json").is_file()
        assert not (stages / "photoset/inner/culled.json").exists()
        assert (downloads / "culled-2.json").is_file()

from pathlib import Path

import pytest
from conftest import Photoset, Tree

from cullen.commands.cull import cull
from cullen.errors import DecisionsFileError


class TestCull:
    def test_moves_source_into_its_category(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "photo_a.NEF": None,
                "photo_b.NEF": None,
            },
            {
                "good": ["photo_a"],
                "bad": ["photo_b"],
            },
        )

        cull(paths=[root])

        assert "good/photo_a.NEF" in tree(root)
        assert "bad/photo_b.NEF" in tree(root)

    def test_sidecar_group_moves_together(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "paired.RAF": None,
                "paired.JPG": None,
                "paired.xmp": None,
                "paired.acr": None,
            },
            {"good": ["paired"]},
        )

        cull(paths=[root])

        assert {"good/paired.RAF", "good/paired.JPG", "good/paired.xmp", "good/paired.acr"} <= tree(root)

    def test_jpeg_without_raw_moves(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"jpeg_only.jpg": None},
            {"good": ["jpeg_only"]},
        )

        cull(paths=[root])

        assert "good/jpeg_only.jpg" in tree(root)

    def test_stem_outside_decisions_stays(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "photo_a.NEF": None,
                "jpeg_only.jpg": None,
            },
            {"good": ["photo_a"]},
        )

        cull(paths=[root])

        assert "jpeg_only.jpg" in tree(root)

    def test_service_folders_are_not_touched(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "photo_a.NEF": None,
                "small": {"photo_a.jpg": None},
                "ondemand": {"photo_a.jpg": None},
                "timelapse": {"frames": {"photo_a.jpg": None}},
            },
            {"good": ["photo_a"]},
        )

        cull(paths=[root])

        after = tree(root)

        assert "small/photo_a.jpg" in after
        assert "ondemand/photo_a.jpg" in after
        assert "timelapse/frames/photo_a.jpg" in after
        assert "culled.json" in after

    def test_nested_folder_gets_its_own_categories(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"sub": {"nested.DNG": None}},
            {"good": ["nested"]},
        )

        cull(paths=[root])

        assert "sub/good/nested.DNG" in tree(root)

    def test_photoset_without_files_at_root(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "part_a": {"photo_a.NEF": None, "photo_a.xmp": None},
                "part_b": {"photo_b.NEF": None},
            },
            {"good": ["photo_a"], "bad": ["photo_b"]},
        )

        cull(paths=[root])

        after = tree(root)

        assert "part_a/good/photo_a.NEF" in after
        assert "part_a/good/photo_a.xmp" in after
        assert "part_b/bad/photo_b.NEF" in after

    def test_deeply_nested_folders_are_reached(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"panorama": {"shot": {"row": {"photo_a.NEF": None}}}},
            {"good": ["photo_a"]},
        )

        cull(paths=[root])

        assert "panorama/shot/row/good/photo_a.NEF" in tree(root)

    def test_service_folder_nested_in_working_folder_is_skipped(
            self,
            photoset: Photoset,
            tree: Tree,
    ) -> None:
        root = photoset(
            {
                "part_a": {
                    "photo_a.NEF": None,
                    "not_signed": {"photo_a.jpg": None},
                },
            },
            {"good": ["photo_a"]},
        )

        cull(paths=[root])

        after = tree(root)

        assert "part_a/good/photo_a.NEF" in after
        assert "part_a/not_signed/photo_a.jpg" in after

    def test_changed_decision_moves_between_categories(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"good": {"photo_d.NEF": None, "photo_d.xmp": None}},
            {"good": [], "bad": ["photo_d"]},
        )

        cull(paths=[root])

        assert {"bad/photo_d.NEF", "bad/photo_d.xmp"} == tree(root) - {"culled.json"}

    def test_second_run_changes_nothing(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "photo_a.NEF": None,
                "sub": {"nested.DNG": None},
            },
            {"good": ["photo_a", "nested"]},
        )

        cull(paths=[root])

        after_first = tree(root)

        cull(paths=[root])

        assert tree(root) == after_first

    def test_categories_are_not_descended_into(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"photo_a.NEF": None},
            {"good": ["photo_a"]},
        )

        cull(paths=[root])

        assert "good/good/photo_a.NEF" not in tree(root)

    def test_folder_with_matching_stem_is_not_moved(self, photoset: Photoset) -> None:
        root = photoset(
            {"photo_a": {"nested.txt": None}},
            {"good": ["photo_a"]},
        )

        cull(paths=[root])

        assert (root / "photo_a").is_dir()

    def test_missing_decisions_file_is_skipped(self, tmp_path: Path, tree: Tree) -> None:
        root = tmp_path / "photoset"

        root.mkdir()

        (root / "photo_a.NEF").touch()

        cull([root])

        assert tree(root) == {"photo_a.NEF"}

    def test_malformed_decisions_file_raises(self, tmp_path: Path) -> None:
        root = tmp_path / "photoset"

        root.mkdir()

        (root / "culled.json").write_text("not json at all")

        with pytest.raises(DecisionsFileError):
            cull([root])


class TestArguments:
    def test_file_is_resolved_against_path(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset({"photo_a.NEF": None}, {"good": ["photo_a"]})

        cull([root], Path("culled.json"))

        assert "good/photo_a.NEF" in tree(root)

    def test_absolute_file_is_used_as_is(self, photoset: Photoset, tree: Tree, tmp_path: Path) -> None:
        root = photoset({"photo_a.NEF": None}, {"good": ["photo_a"]})

        outside = tmp_path / "outside.json"

        outside.write_text((root / "culled.json").read_text())

        cull([root], outside)

        assert "good/photo_a.NEF" in tree(root)

    def test_path_defaults_to_cwd(
            self,
            photoset: Photoset,
            tree: Tree,
            monkeypatch: "pytest.MonkeyPatch",
    ) -> None:
        root = photoset({"photo_a.NEF": None}, {"good": ["photo_a"]})

        monkeypatch.chdir(root)

        cull()

        assert "good/photo_a.NEF" in tree(root)

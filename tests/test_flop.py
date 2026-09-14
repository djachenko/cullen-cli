from pathlib import Path

import pytest
from conftest import Photoset, Tree

from cullen.commands.cull import cull
from cullen.commands.flop import flop
from cullen.errors import DecisionsFileError, FlopError


class TestFlop:
    def test_category_moves_to_the_top(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"part_a": {"good": {"photo_a.NEF": None}}},
            {"good": ["photo_a"]},
        )

        flop(root)

        assert "good/part_a/photo_a.NEF" in tree(root)

    def test_path_below_category_is_preserved(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"panorama": {"shot": {"bad": {"photo_b.NEF": None}}}},
            {"bad": ["photo_b"]},
        )

        flop(root)

        assert "bad/panorama/shot/photo_b.NEF" in tree(root)

    def test_file_outside_categories_stays(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"part_a": {"photo_c.NEF": None}},
            {"good": ["photo_a"]},
        )

        flop(root)

        assert "part_a/photo_c.NEF" in tree(root)

    def test_sidecars_follow_their_source(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"part_a": {"good": {"paired.RAF": None, "paired.xmp": None}}},
            {"good": ["paired"]},
        )

        flop(root)

        assert {"good/part_a/paired.RAF", "good/part_a/paired.xmp"} <= tree(root)

    def test_second_run_changes_nothing(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "part_a": {"good": {"photo_a.NEF": None}},
                "part_b": {"bad": {"photo_b.NEF": None}},
            },
            {"good": ["photo_a"], "bad": ["photo_b"]},
        )

        flop(root)

        after_first = tree(root)

        flop(root)

        assert tree(root) == after_first

    def test_two_categories_in_path_raise(self, photoset: Photoset) -> None:
        root = photoset(
            {"part_a": {"bad": {"good": {"photo_c.NEF": None}}}},
            {"good": [], "bad": []},
        )

        with pytest.raises(FlopError):
            flop(root)

    def test_repeated_category_raises(self, photoset: Photoset) -> None:
        root = photoset(
            {"good": {"part_a": {"good": {"photo_c.NEF": None}}}},
            {"good": []},
        )

        with pytest.raises(FlopError):
            flop(root)

    def test_nothing_moves_when_validation_fails(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "part_a": {"good": {"photo_a.NEF": None}},
                "part_b": {"bad": {"good": {"photo_c.NEF": None}}},
            },
            {"good": [], "bad": []},
        )

        before = tree(root)

        with pytest.raises(FlopError):
            flop(root)

        assert tree(root) == before


class TestCategories:
    def test_categories_come_from_the_decisions_file(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"part_a": {"maybe": {"photo_a.NEF": None}}},
            {"maybe": ["photo_a"]},
        )

        flop(root)

        assert "maybe/part_a/photo_a.NEF" in tree(root)

    def test_folder_outside_the_decisions_file_is_not_a_category(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"part_a": {"good": {"photo_a.NEF": None}}},
            {"maybe": ["photo_a"]},
        )

        flop(root)

        assert "part_a/good/photo_a.NEF" in tree(root)

    def test_missing_decisions_file_raises(self, tmp_path: Path) -> None:
        root = tmp_path / "photoset"

        root.mkdir()

        with pytest.raises(DecisionsFileError):
            flop(root)


class TestAfterCull:
    def test_flop_inverts_what_cull_produced(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "part_a": {"photo_a.NEF": None},
                "part_b": {"photo_b.NEF": None},
            },
            {"good": ["photo_a"], "bad": ["photo_b"]},
        )

        cull(paths=[root])

        assert {"part_a/good/photo_a.NEF", "part_b/bad/photo_b.NEF"} <= tree(root)

        flop(root)

        after = tree(root)

        assert "good/part_a/photo_a.NEF" in after
        assert "bad/part_b/photo_b.NEF" in after

    def test_deeply_nested_cull_result_is_flopped(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"panorama": {"shot": {"row": {"photo_a.NEF": None}}}},
            {"good": ["photo_a"]},
        )

        cull(paths=[root])

        flop(root)

        assert "good/panorama/shot/row/photo_a.NEF" in tree(root)


class TestDryRun:
    def test_nothing_moves(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"part_a": {"good": {"photo_a.NEF": None}}},
            {"good": ["photo_a"]},
        )

        flop(root, dry_run=True)

        assert "part_a/good/photo_a.NEF" in tree(root)

    def test_planned_move_is_printed(self, photoset: Photoset, capsys: pytest.CaptureFixture[str]) -> None:
        root = photoset(
            {"part_a": {"good": {"photo_a.NEF": None}}},
            {"good": ["photo_a"]},
        )

        flop(root, dry_run=True)

        output = capsys.readouterr().out

        assert str(Path("part_a/good/photo_a.NEF")) in output
        assert str(Path("good/part_a/photo_a.NEF")) in output

    def test_untouched_file_is_not_printed(self, photoset: Photoset, capsys: pytest.CaptureFixture[str]) -> None:
        root = photoset(
            {"part_a": {"photo_c.NEF": None}},
            {"good": ["photo_a"]},
        )

        flop(root, dry_run=True)

        assert "photo_c.NEF" not in capsys.readouterr().out


class TestOutput:
    def test_summary_reports_moves(self, photoset: Photoset, capsys: pytest.CaptureFixture[str]) -> None:
        root = photoset(
            {"part_a": {"good": {"photo_a.NEF": None}}},
            {"good": ["photo_a"]},
        )

        flop(root)

        output = capsys.readouterr().out

        assert "files" in output
        assert "moved" in output

    def test_dry_run_summary_says_to_move(self, photoset: Photoset, capsys: pytest.CaptureFixture[str]) -> None:
        root = photoset(
            {"part_a": {"good": {"photo_a.NEF": None}}},
            {"good": ["photo_a"]},
        )

        flop(root, dry_run=True)

        assert "to move" in capsys.readouterr().out


class TestServiceFolders:
    def test_category_inside_service_folder_stays(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"small": {"good": {"photo_a.jpg": None}}},
            {"good": ["photo_a"]},
        )

        flop(root)

        assert "small/good/photo_a.jpg" in tree(root)

    def test_service_folder_nested_in_working_folder_is_skipped(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "part_a": {
                    "good": {"photo_a.NEF": None},
                    "not_signed": {"good": {"photo_a.jpg": None}},
                },
            },
            {"good": ["photo_a"]},
        )

        flop(root)

        after = tree(root)

        assert "good/part_a/photo_a.NEF" in after
        assert "part_a/not_signed/good/photo_a.jpg" in after

    def test_two_categories_inside_service_folder_do_not_raise(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {"timelapse": {"bad": {"good": {"photo_c.jpg": None}}}},
            {"good": [], "bad": []},
        )

        flop(root)

        assert "timelapse/bad/good/photo_c.jpg" in tree(root)

    def test_cull_and_flop_leave_service_folders_alone(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "part_a": {"photo_a.NEF": None},
                "small": {"photo_a.jpg": None},
                "ondemand": {"photo_a.jpg": None},
            },
            {"good": ["photo_a"]},
        )

        cull(paths=[root])
        flop(root)

        after = tree(root)

        assert "good/part_a/photo_a.NEF" in after
        assert "small/photo_a.jpg" in after
        assert "ondemand/photo_a.jpg" in after


class TestCollisions:
    def test_two_sources_landing_on_one_path_raise(self, photoset: Photoset) -> None:
        root = photoset(
            {
                "part_a": {"good": {"photo_a.NEF": None}},
                "good": {"part_a": {"photo_a.NEF": None}},
            },
            {"good": ["photo_a"]},
        )

        with pytest.raises(FlopError):
            flop(root)

    def test_nothing_moves_on_collision(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "part_a": {"good": {"photo_a.NEF": None}},
                "good": {"part_a": {"photo_a.NEF": None}},
                "part_b": {"bad": {"photo_b.NEF": None}},
            },
            {"good": ["photo_a"], "bad": ["photo_b"]},
        )

        before = tree(root)

        with pytest.raises(FlopError):
            flop(root)

        assert tree(root) == before

    def test_error_names_both_sources(self, photoset: Photoset) -> None:
        root = photoset(
            {
                "part_a": {"good": {"photo_a.NEF": None}},
                "good": {"part_a": {"photo_a.NEF": None}},
            },
            {"good": ["photo_a"]},
        )

        with pytest.raises(FlopError) as error:
            flop(root)

        message = str(error.value)

        assert str(Path("part_a/good/photo_a.NEF")) in message
        assert str(Path("good/part_a/photo_a.NEF")) in message

    def test_same_name_in_different_folders_is_not_a_collision(self, photoset: Photoset, tree: Tree) -> None:
        root = photoset(
            {
                "part_a": {"good": {"photo_a.NEF": None}},
                "part_b": {"good": {"photo_a.NEF": None}},
            },
            {"good": ["photo_a"]},
        )

        flop(root)

        after = tree(root)

        assert "good/part_a/photo_a.NEF" in after
        assert "good/part_b/photo_a.NEF" in after

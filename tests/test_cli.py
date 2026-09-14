from pathlib import Path

import pytest
from typer.testing import CliRunner

from cullen._cli.main import app, main
from cullen.errors import DecisionsFileError, FlopError

runner = CliRunner()


class TestCli:
    def test_no_arguments_shows_help(self) -> None:
        result = runner.invoke(app, [])

        assert "cull" in result.output
        assert "relocate" in result.output
        assert "flop" in result.output

    def test_cull_is_registered(self) -> None:
        assert runner.invoke(app, ["cull", "--help"]).exit_code == 0

    def test_flop_is_registered(self) -> None:
        assert runner.invoke(app, ["flop", "--help"]).exit_code == 0

    def test_relocate_is_registered(self) -> None:
        assert runner.invoke(app, ["relocate", "--help"]).exit_code == 0

    def test_relocate_requires_arguments(self) -> None:
        assert runner.invoke(app, ["relocate"]).exit_code != 0

    def test_missing_file_warns_and_skips(self, tmp_path) -> None:
        result = runner.invoke(app, ["cull", str(tmp_path)])

        assert result.exit_code == 0
        assert "culled.json" in result.stdout

    def test_malformed_file_reports_path_and_exits(self, tmp_path) -> None:
        (tmp_path / "culled.json").write_text("not json at all")

        result = runner.invoke(app, ["cull", str(tmp_path)])

        assert isinstance(result.exception, DecisionsFileError)
        assert "culled.json" in str(result.exception)

    def test_cull_runs_through_the_cli(self, photoset, tree) -> None:
        root = photoset({"photo_a.NEF": None}, {"good": ["photo_a"]})

        result = runner.invoke(app, ["cull", str(root)])

        assert result.exit_code == 0
        assert "good/photo_a.NEF" in tree(root)

    def test_flop_runs_through_the_cli(self, photoset, tree) -> None:
        root = photoset({"part_a": {"good": {"photo_a.NEF": None}}}, {"good": ["photo_a"]})

        result = runner.invoke(app, ["flop", str(root)])

        assert result.exit_code == 0
        assert "good/part_a/photo_a.NEF" in tree(root)

    def test_flop_dry_run_reports_without_moving(self, photoset, tree) -> None:
        root = photoset({"part_a": {"good": {"photo_a.NEF": None}}}, {"good": ["photo_a"]})

        result = runner.invoke(app, ["flop", str(root), "--dry-run"])

        assert result.exit_code == 0
        assert str(Path("good/part_a/photo_a.NEF")) in result.output
        assert "part_a/good/photo_a.NEF" in tree(root)

    def test_flop_reports_multiple_categories_and_exits(self, photoset) -> None:
        root = photoset({"part_a": {"bad": {"good": {"photo_c.NEF": None}}}}, {"good": [], "bad": []})

        result = runner.invoke(app, ["flop", str(root)])

        assert isinstance(result.exception, FlopError)
        assert "multiple categories" in str(result.exception)


class TestMain:
    def test_cullen_error_is_reported_and_exits(self, tmp_path, monkeypatch, capsys) -> None:
        (tmp_path / "culled.json").write_text("not json at all")

        monkeypatch.setattr("sys.argv", ["cullen", "cull", str(tmp_path)])

        with pytest.raises(SystemExit) as info:
            main()

        assert info.value.code == 1
        assert "culled.json" in capsys.readouterr().err

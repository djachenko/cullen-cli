from pathlib import Path

import pytest
from test_relocate import write_decisions
from typer.testing import CliRunner

from cullen._cli.main import app, main
from cullen.errors import DecisionsFileError, FlopError

runner = CliRunner()


@pytest.fixture
def walked(monkeypatch) -> list[Path]:
    roots: list[Path] = []

    monkeypatch.setattr("cullen._cli.commands.relocate.bfs", lambda root, provider: roots.append(root))

    return roots


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

    def test_relocate_without_arguments_scans_cwd_from_root(self, tmp_path, monkeypatch, walked) -> None:
        monkeypatch.chdir(tmp_path)
        write_decisions(tmp_path / "culled-1.json", "photoset")

        result = runner.invoke(app, ["relocate"])

        assert result.exit_code == 0
        assert walked == [Path("/")]

    def test_relocate_with_path_scans_it_from_root(self, tmp_path, walked) -> None:
        write_decisions(tmp_path / "culled-1.json", "photoset")

        result = runner.invoke(app, ["relocate", str(tmp_path)])

        assert result.exit_code == 0
        assert walked == [Path("/")]

    def test_relocate_with_root_scans_root(self, tmp_path, walked) -> None:
        downloads = tmp_path / "downloads"
        stages = tmp_path / "stages"

        downloads.mkdir()
        stages.mkdir()
        write_decisions(downloads / "culled-1.json", "photoset")

        result = runner.invoke(app, ["relocate", str(downloads), "--root", str(stages)])

        assert result.exit_code == 0
        assert walked == [stages]

    def test_relocate_with_files_scans_from_root(self, tmp_path, walked) -> None:
        file_a = write_decisions(tmp_path / "culled-1.json", "photoset_a")
        file_b = write_decisions(tmp_path / "culled-2.json", "photoset_b")

        result = runner.invoke(app, ["relocate", str(file_a), str(file_b)])

        assert result.exit_code == 0
        assert walked == [Path("/")]

    def test_relocate_with_files_and_root_scans_root(self, tmp_path, walked) -> None:
        stages = tmp_path / "stages"

        stages.mkdir()
        file_a = write_decisions(tmp_path / "culled-1.json", "photoset_a")
        file_b = write_decisions(tmp_path / "culled-2.json", "photoset_b")

        result = runner.invoke(app, ["relocate", str(file_a), str(file_b), "--root", str(stages)])

        assert result.exit_code == 0
        assert walked == [stages]

    def test_relocate_runs_through_the_cli(self, tmp_path, create_files) -> None:
        downloads = tmp_path / "downloads"
        stages = tmp_path / "stages"

        downloads.mkdir()
        create_files(stages, {"photoset": {"cullen": {}}})
        write_decisions(downloads / "culled-1.json", "photoset")

        result = runner.invoke(app, ["relocate", str(downloads), "--root", str(stages)])

        assert result.exit_code == 0
        assert (stages / "photoset/culled.json").is_file()

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

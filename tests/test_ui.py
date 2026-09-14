import pytest

from cullen.ui import Console, PlainConsole, RichConsole, make_console


class TestPlainConsole:
    def test_line_is_printed_as_is(self, capsys: pytest.CaptureFixture[str]) -> None:
        PlainConsole().line("part_a/good/photo_a.NEF → good/part_a/photo_a.NEF")

        assert capsys.readouterr().out.strip() == "part_a/good/photo_a.NEF → good/part_a/photo_a.NEF"

    def test_style_does_not_leak_into_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        PlainConsole().line("relocated", style="green")

        assert capsys.readouterr().out.strip() == "relocated"

    def test_summary_aligns_labels(self, capsys: pytest.CaptureFixture[str]) -> None:
        PlainConsole().summary([("files", "5"), ("to move", "3")])

        assert capsys.readouterr().out == "files    5\nto move  3\n"

    def test_empty_summary_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        PlainConsole().summary([])

        assert capsys.readouterr().out == ""

    def test_progress_reports_every_step(self, capsys: pytest.CaptureFixture[str]) -> None:
        with PlainConsole().progress("photoset", total=2) as task:
            task.describe("photo_a.NEF")
            task.advance()
            task.describe("photo_b.NEF")
            task.advance()

        assert capsys.readouterr().out == "photoset\nphoto_a.NEF\nphoto_b.NEF\n"

    def test_advance_alone_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        with PlainConsole().progress("photoset", total=2) as task:
            task.advance()
            task.advance()

        assert capsys.readouterr().out == "photoset\n"


class TestRichConsole:
    def test_summary_renders_labels_and_values(self, capsys: pytest.CaptureFixture[str]) -> None:
        RichConsole().summary([("files", "5"), ("moved", "3")])

        output = capsys.readouterr().out

        assert "files" in output
        assert "moved" in output
        assert "3" in output

    def test_progress_survives_a_run(self, capsys: pytest.CaptureFixture[str]) -> None:
        with RichConsole().progress("photoset", total=1) as task:
            task.describe("photo_a.NEF")
            task.advance()

        assert isinstance(capsys.readouterr().out, str)


class TestMakeConsole:
    def test_plain_console_outside_a_terminal(self) -> None:
        assert isinstance(make_console(), PlainConsole)

    def test_rich_console_in_a_terminal(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.stdout.isatty", lambda: True)

        assert isinstance(make_console(), RichConsole)

    def test_both_implement_the_abstraction(self) -> None:
        assert issubclass(PlainConsole, Console)
        assert issubclass(RichConsole, Console)

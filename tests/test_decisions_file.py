from pathlib import Path

import pytest

from cullen.decisions_file import load
from cullen.errors import DecisionsFileError, DecisionsFileMissingError


class TestLoad:
    def test_missing_file_raises_missing(self, tmp_path: Path) -> None:
        with pytest.raises(DecisionsFileMissingError):
            load(tmp_path / "culled.json")

    def test_malformed_file_raises_but_not_missing(self, tmp_path: Path) -> None:
        path = tmp_path / "culled.json"

        path.write_text("not json at all")

        with pytest.raises(DecisionsFileError) as info:
            load(path)

        assert not isinstance(info.value, DecisionsFileMissingError)

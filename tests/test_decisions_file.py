from pathlib import Path

import pytest

from cullen import CullenDecisions, CullenDecisionsError, CullenDecisionsMissingError


class TestLoad:
    def test_missing_file_raises_missing(self, tmp_path: Path) -> None:
        with pytest.raises(CullenDecisionsMissingError):
            CullenDecisions.load(tmp_path / "culled.json")

    def test_malformed_file_raises_but_not_missing(self, tmp_path: Path) -> None:
        path = tmp_path / "culled.json"

        path.write_text("not json at all")

        with pytest.raises(CullenDecisionsError) as info:
            CullenDecisions.load(path)

        assert not isinstance(info.value, CullenDecisionsMissingError)

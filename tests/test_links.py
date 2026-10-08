import json
from pathlib import Path

from cullen import CullenLinks


class TestSave:
    def test_set_file_named_after_set(self, tmp_path: Path) -> None:
        CullenLinks("25.09.13.console_flight", None, {}).save(tmp_path)

        assert (tmp_path / "25.09.13.console_flight.json").is_file()

    def test_part_file_named_set_dot_part(self, tmp_path: Path) -> None:
        CullenLinks("25.09.13.console_flight", "1.singles", {}).save(tmp_path)

        assert (tmp_path / "25.09.13.console_flight.1.singles.json").is_file()

    def test_writes_bare_list_of_name_and_url(self, tmp_path: Path) -> None:
        CullenLinks("photoset", None, {"ZSC_1": "https://a", "ZSC_2": "https://b"}).save(tmp_path)

        assert json.loads((tmp_path / "photoset.json").read_text()) == [
            {"name": "ZSC_1", "url": "https://a"},
            {"name": "ZSC_2", "url": "https://b"},
        ]

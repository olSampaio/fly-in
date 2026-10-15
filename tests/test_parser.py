from pathlib import Path

import pytest

from flyin.errors import ParseError
from flyin.parser import MapParser


def test_duplicate_start_reports_line(tmp_path: Path) -> None:
    map_file = tmp_path / "map.txt"
    map_file.write_text(
        "nb_drones: 1\nstart_hub: s 0 0\nstart_hub: t 1 0\n"
    )
    with pytest.raises(ParseError) as info:
        MapParser().parse(str(map_file))
    assert info.value.line == 3
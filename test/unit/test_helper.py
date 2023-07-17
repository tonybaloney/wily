from io import BytesIO, TextIOWrapper
from unittest import mock

from wily.config import DEFAULT_GRID_STYLE
from wily.helper import get_style


def test_get_style():
    output = TextIOWrapper(BytesIO(), encoding="utf-8")
    with mock.patch("sys.stdout", output):
        style = get_style()
    assert style == DEFAULT_GRID_STYLE


def test_get_style_charmap():
    output = TextIOWrapper(BytesIO(), encoding="charmap")
    with mock.patch("sys.stdout", output):
        style = get_style()
    assert style == "grid"


def test_get_style_charmap_not_default_grid_style():
    output = TextIOWrapper(BytesIO(), encoding="charmap")
    with mock.patch("sys.stdout", output):
        style = get_style("something_else")
    assert style == "something_else"

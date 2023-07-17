from io import BytesIO, StringIO, TextIOWrapper
from unittest import mock

from wily.config import DEFAULT_GRID_STYLE
from wily.helper import get_style
from wily.helper.output import print_result

HEADERS = ("header1", "header2", "header3")
DATA = [
    ("data1_1", "data1_2", "data1_3"),
    ("data2_1", "data2_2", "data2_3"),
]

_TABLE_DATA = """
╒═══════════╤═══════════╤═══════════╕
│ header1   │ header2   │ header3   │
╞═══════════╪═══════════╪═══════════╡
│ data1_1   │ data1_2   │ data1_3   │
├───────────┼───────────┼───────────┤
│ data2_1   │ data2_2   │ data2_3   │
╘═══════════╧═══════════╧═══════════╛
"""

TABLE_DATA = _TABLE_DATA[1:]

JSON_DATA = """[
  {
    "header1": "data1_1",
    "header2": "data1_2",
    "header3": "data1_3"
  },
  {
    "header1": "data2_1",
    "header2": "data2_2",
    "header3": "data2_3"
  }
]
"""

JSON_DATA_WITH_PATH = """[
  {
    "header1": "data1_1",
    "header2": "data1_2",
    "header3": "data1_3",
    "Filename": "some_path"
  },
  {
    "header1": "data2_1",
    "header2": "data2_2",
    "header3": "data2_3",
    "Filename": "some_path"
  }
]
"""


def test_print_result_empty_json():
    stdout = StringIO()
    with mock.patch("sys.stdout", stdout):
        print_result(True, [], (), DEFAULT_GRID_STYLE)
    assert stdout.getvalue() == "[]\n"


def test_print_result_empty_table():
    stdout = StringIO()
    with mock.patch("sys.stdout", stdout):
        print_result(False, [], (), DEFAULT_GRID_STYLE)
    assert stdout.getvalue() == "\n"


def test_print_result_data_json():
    stdout = StringIO()
    with mock.patch("sys.stdout", stdout):
        print_result(True, DATA, HEADERS, DEFAULT_GRID_STYLE)
    assert stdout.getvalue() == JSON_DATA


def test_print_result_data_table():
    stdout = StringIO()
    with mock.patch("sys.stdout", stdout):
        print_result(False, DATA, HEADERS, DEFAULT_GRID_STYLE)
    assert stdout.getvalue() == TABLE_DATA


def test_print_result_data_json_path():
    stdout = StringIO()
    with mock.patch("sys.stdout", stdout):
        print_result(True, DATA, HEADERS, DEFAULT_GRID_STYLE, "some_path")
    assert stdout.getvalue() == JSON_DATA_WITH_PATH


def test_print_result_data_table_path():
    stdout = StringIO()
    with mock.patch("sys.stdout", stdout):
        print_result(False, DATA, HEADERS, DEFAULT_GRID_STYLE, "some_path")
    assert stdout.getvalue() == TABLE_DATA


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

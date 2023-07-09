from io import StringIO
from unittest import mock

from wily.config import DEFAULT_GRID_STYLE
from wily.helper.output import print_result

HEADERS = ("header1", "header2", "header3")
DATA = [
    ("data1_1", "data1_2", "data1_3"),
    ("data2_1", "data2_2", "data2_3"),
]


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
    assert stdout.getvalue() == """[
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


def test_print_result_data_table():
    stdout = StringIO()
    with mock.patch("sys.stdout", stdout):
        print_result(False, DATA, HEADERS, DEFAULT_GRID_STYLE)
    assert stdout.getvalue() == """
╒═══════════╤═══════════╤═══════════╕
│ header1   │ header2   │ header3   │
╞═══════════╪═══════════╪═══════════╡
│ data1_1   │ data1_2   │ data1_3   │
├───────────┼───────────┼───────────┤
│ data2_1   │ data2_2   │ data2_3   │
╘═══════════╧═══════════╧═══════════╛
"""[1:]


def test_print_result_data_json_path():
    stdout = StringIO()
    with mock.patch("sys.stdout", stdout):
        print_result(True, DATA, HEADERS, DEFAULT_GRID_STYLE, "some_path")
    assert stdout.getvalue() == """[
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


def test_print_result_data_table_path():
    stdout = StringIO()
    with mock.patch("sys.stdout", stdout):
        print_result(False, DATA, HEADERS, DEFAULT_GRID_STYLE, "some_path")
    assert stdout.getvalue() == """
╒═══════════╤═══════════╤═══════════╕
│ header1   │ header2   │ header3   │
╞═══════════╪═══════════╪═══════════╡
│ data1_1   │ data1_2   │ data1_3   │
├───────────┼───────────┼───────────┤
│ data2_1   │ data2_2   │ data2_3   │
╘═══════════╧═══════════╧═══════════╛
"""[1:]

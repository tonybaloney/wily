from io import BytesIO, StringIO, TextIOWrapper
from unittest import mock

import tabulate

from wily.defaults import DEFAULT_GRID_STYLE
from wily.helper import get_maxcolwidth, get_style

SHORT_DATA = [list("abcdefgh"), list("abcdefgh")]

MEDIUM_DATA = [["medium_data"] * 2, ["medium_data"] * 2]

LONG_DATA = [["long_data"] * 8, ["long_data"] * 8]

HUGE_DATA = [["huge_data"] * 18, ["huge_data"] * 18]

LONG_LINE_MEDIUM_DATA = [
    ["long_line_for_some_medium_data"] * 2,
    ["long_line_for_some_medium_data"] * 2,
]


def test_get_maxcolwidth_no_wrap():
    result = get_maxcolwidth([], False)
    assert result is None


def test_get_maxcolwidth_wrap_short():
    for width in range(35, 100):
        mock_get_terminal_size = mock.Mock(return_value=(width, 24))
        mock_shutil = mock.Mock(get_terminal_size=mock_get_terminal_size)

        with mock.patch("wily.helper.shutil", mock_shutil):
            result = get_maxcolwidth(SHORT_DATA[0], True)
        as_table = tabulate.tabulate(
            tabular_data=SHORT_DATA,
            tablefmt="grid",
            maxcolwidths=result,
            maxheadercolwidths=result,
        )

        line = as_table.splitlines()[0]
        assert len(line) < width
        assert len(line) >= width / 3


def test_get_maxcolwidth_wrap_medium():
    for width in range(35, 100):
        mock_get_terminal_size = mock.Mock(return_value=(width, 24))
        mock_shutil = mock.Mock(get_terminal_size=mock_get_terminal_size)

        with mock.patch("wily.helper.shutil", mock_shutil):
            result = get_maxcolwidth(MEDIUM_DATA[0], True)
        as_table = tabulate.tabulate(
            tabular_data=MEDIUM_DATA,
            tablefmt="grid",
            maxcolwidths=result,
            maxheadercolwidths=result,
        )

        line = as_table.splitlines()[0]
        print(line)
        print(width, len(line))
        assert len(line) < width
        if width < 85:
            assert len(line) >= width / 3


def test_get_maxcolwidth_wrap_long_line_medium():
    for width in range(35, 100):
        mock_get_terminal_size = mock.Mock(return_value=(width, 24))
        mock_shutil = mock.Mock(get_terminal_size=mock_get_terminal_size)

        with mock.patch("wily.helper.shutil", mock_shutil):
            result = get_maxcolwidth(LONG_LINE_MEDIUM_DATA[0], True)
        as_table = tabulate.tabulate(
            tabular_data=LONG_LINE_MEDIUM_DATA,
            tablefmt="grid",
            maxcolwidths=result,
            maxheadercolwidths=result,
        )

        line = as_table.splitlines()[0]
        print(line)
        print(width, len(line))
        assert len(line) < width
        if width < 85:
            assert len(line) >= width / 3


def test_get_maxcolwidth_wrap_long():
    for width in range(35, 290):
        mock_get_terminal_size = mock.Mock(return_value=(width, 24))
        mock_shutil = mock.Mock(get_terminal_size=mock_get_terminal_size)

        with mock.patch("wily.helper.shutil", mock_shutil):
            result = get_maxcolwidth(LONG_DATA[0], True)
        as_table = tabulate.tabulate(
            tabular_data=LONG_DATA,
            tablefmt="grid",
            maxcolwidths=result,
            maxheadercolwidths=result,
        )

        line = as_table.splitlines()[0]
        assert len(line) < width
        if width < 290:
            assert len(line) >= width / 3


def test_get_maxcolwidth_wrap_huge():
    for width in range(75, 450):
        mock_get_terminal_size = mock.Mock(return_value=(width, 24))
        mock_shutil = mock.Mock(get_terminal_size=mock_get_terminal_size)

        with mock.patch("wily.helper.shutil", mock_shutil):
            result = get_maxcolwidth(HUGE_DATA[0], True)
        as_table = tabulate.tabulate(
            tabular_data=HUGE_DATA,
            tablefmt="grid",
            maxcolwidths=result,
            maxheadercolwidths=result,
        )

        line = as_table.splitlines()[0]
        assert len(line) < width
        if width < 220:
            assert len(line) >= width / 3
        else:
            assert len(line) >= width / 4


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


def test_get_style_none():
    output = StringIO()  # output.encoding is None
    with mock.patch("sys.stdout", output):
        style = get_style()
    assert style == "fancy_grid"

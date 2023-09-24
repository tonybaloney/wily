"""Unit tests for the graph command."""

from unittest import mock

from util import get_mock_state_and_config

from wily import format_datetime
from wily.commands.graph import graph, metric_parts

SCATTER_EXPECTED = {
    "x": [format_datetime(0)],
    "y": [0],
    "mode": "lines+markers",
    "name": "test.py",
    "ids": ("abcdeff",),
    "text": ["Author 0 <br>Message 0"],
    "marker": {"size": 0, "color": [0]},
    "xcalendar": "gregorian",
    "hoveron": "points+fills",
}

LAYOUT_EXPECTED = {
    "title": "History of Lines of Code for test.py",
    "xaxis": {"title": "history"},
    "yaxis": {"title": "Lines of Code"},
}


def test_graph():
    metrics = "raw.loc"
    path = ("test.py",)
    output = ""
    mock_State, mock_config = get_mock_state_and_config(3, ascending=True)
    mock_offline = mock.MagicMock()
    mock_layout = mock.MagicMock()
    mock_Layout = mock.MagicMock(return_value=mock_layout)
    mock_scatter = mock.MagicMock()
    mock_Scatter = mock.MagicMock(return_value=mock_scatter)
    mock_go = mock.MagicMock()
    mock_go.Layout = mock_Layout
    mock_go.Scatter = mock_Scatter
    mock.seal(mock_go)

    with mock.patch("wily.commands.graph.plotly.offline", mock_offline), mock.patch(
        "wily.commands.graph.go", mock_go
    ), mock.patch("wily.commands.graph.State", mock_State):
        graph(
            config=mock_config,
            path=path,
            metrics=metrics,
            output=output,
            x_axis=None,
            changes=True,
            aggregate=False,
        )

    mock_offline.plot.assert_called_once_with(
        {"data": [mock_scatter], "layout": mock_layout},
        auto_open=True,
        filename="wily-report.html",
        include_plotlyjs=True,
    )
    mock_Layout.assert_called_once_with(**LAYOUT_EXPECTED)
    mock_go.Scatter.assert_called_once_with(**SCATTER_EXPECTED)
    mock_State.assert_called_once_with(mock_config)


SCATTER_EXPECTED_WITH_KEYERROR = {
    "x": [format_datetime(0)],
    "y": [0],
    "mode": "lines+markers",
    "name": "test.py",
    "ids": ("abcdeff",),
    "text": ["Author 0 <br>Message 0"],
    "marker": {"size": 0, "color": [0]},
    "xcalendar": "gregorian",
    "hoveron": "points+fills",
}

LAYOUT_EXPECTED_WITH_KEYERROR = {
    "title": "History of Lines of Code for test.py",
    "xaxis": {"title": "history"},
    "yaxis": {"title": "Lines of Code"},
}


def test_graph_with_keyerror():
    metrics = "raw.loc"
    path = ("test.py",)
    output = ""
    mock_State, mock_config = get_mock_state_and_config(
        3, ascending=True, with_keyerror=True
    )
    mock_offline = mock.MagicMock()
    mock_layout = mock.MagicMock()
    mock_Layout = mock.MagicMock(return_value=mock_layout)
    mock_scatter = mock.MagicMock()
    mock_Scatter = mock.MagicMock(return_value=mock_scatter)
    mock_go = mock.MagicMock()
    mock_go.Layout = mock_Layout
    mock_go.Scatter = mock_Scatter
    mock.seal(mock_go)

    with mock.patch("wily.commands.graph.plotly.offline", mock_offline), mock.patch(
        "wily.commands.graph.go", mock_go
    ), mock.patch("wily.commands.graph.State", mock_State):
        graph(
            config=mock_config,
            path=path,
            metrics=metrics,
            output=output,
            x_axis=None,
            changes=True,
            aggregate=False,
        )

    mock_offline.plot.assert_called_once_with(
        {"data": [mock_scatter], "layout": mock_layout},
        auto_open=True,
        filename="wily-report.html",
        include_plotlyjs=True,
    )
    mock_Layout.assert_called_once_with(**LAYOUT_EXPECTED_WITH_KEYERROR)
    mock_go.Scatter.assert_called_once_with(**SCATTER_EXPECTED_WITH_KEYERROR)
    mock_State.assert_called_once_with(mock_config)


SCATTER_EXPECTED_WITH_CHANGES = {
    "x": [
        format_datetime(0),
        format_datetime(1),
        format_datetime(2),
        format_datetime(10),
        format_datetime(10),
        format_datetime(10),
    ],
    "y": [0, 1, 2, 3, 4, 3],
    "mode": "lines+markers",
    "name": "test.py",
    "ids": ("abcdeff",),
    "text": [
        "Author 0 <br>Message 0",
        "Author 1 <br>Message 1",
        "Author 2 <br>Message 2",
        "Author Someone <br>Message here.",
        "Author Someone <br>Message here.",
        "Author Someone <br>Message here.",
    ],
    "marker": {"size": 0, "color": [0, 1, 2, 3, 4, 5]},
    "xcalendar": "gregorian",
    "hoveron": "points+fills",
}

LAYOUT_EXPECTED_WITH_CHANGES = {
    "title": "History of Lines of Code for test.py",
    "xaxis": {"title": "history"},
    "yaxis": {"title": "Lines of Code"},
}


def test_graph_with_changes():
    metrics = "raw.loc"
    path = ("test.py",)
    output = ""
    mock_State, mock_config = get_mock_state_and_config(3)
    mock_offline = mock.MagicMock()
    mock_layout = mock.MagicMock()
    mock_Layout = mock.MagicMock(return_value=mock_layout)
    mock_scatter = mock.MagicMock()
    mock_Scatter = mock.MagicMock(return_value=mock_scatter)
    mock_go = mock.MagicMock()
    mock_go.Layout = mock_Layout
    mock_go.Scatter = mock_Scatter
    mock.seal(mock_go)

    with mock.patch("wily.commands.graph.plotly.offline", mock_offline), mock.patch(
        "wily.commands.graph.go", mock_go
    ), mock.patch("wily.commands.graph.State", mock_State):
        graph(
            config=mock_config,
            path=path,
            metrics=metrics,
            output=output,
            x_axis=None,
            changes=True,
            aggregate=False,
        )

    mock_offline.plot.assert_called_once_with(
        {"data": [mock_scatter], "layout": mock_layout},
        auto_open=True,
        filename="wily-report.html",
        include_plotlyjs=True,
    )
    mock_Layout.assert_called_once_with(**LAYOUT_EXPECTED_WITH_CHANGES)
    mock_go.Scatter.assert_called_once_with(**SCATTER_EXPECTED_WITH_CHANGES)
    mock_State.assert_called_once_with(mock_config)


SCATTER_EXPECTED_ALL = {
    "x": [
        format_datetime(0),
        format_datetime(1),
        format_datetime(2),
        format_datetime(10),
        format_datetime(10),
        format_datetime(10),
        format_datetime(10),
    ],
    "y": [0, 1, 2, 3, 4, 3, 3],
    "mode": "lines+markers",
    "name": "test.py",
    "ids": ("abcdeff",),
    "text": [
        "Author 0 <br>Message 0",
        "Author 1 <br>Message 1",
        "Author 2 <br>Message 2",
        "Author Someone <br>Message here.",
        "Author Someone <br>Message here.",
        "Author Someone <br>Message here.",
        "Author Someone <br>Message here.",
    ],
    "marker": {"size": 0, "color": [0, 1, 2, 3, 4, 5, 6]},
    "xcalendar": "gregorian",
    "hoveron": "points+fills",
}

LAYOUT_EXPECTED_ALL = {
    "title": "History of Lines of Code for test.py",
    "xaxis": {"title": "history"},
    "yaxis": {"title": "Lines of Code"},
}


def test_graph_all():
    metrics = "raw.loc"
    path = ("test.py",)
    output = ""
    mock_State, mock_config = get_mock_state_and_config(3)
    mock_offline = mock.MagicMock()
    mock_layout = mock.MagicMock()
    mock_Layout = mock.MagicMock(return_value=mock_layout)
    mock_scatter = mock.MagicMock()
    mock_Scatter = mock.MagicMock(return_value=mock_scatter)
    mock_go = mock.MagicMock()
    mock_go.Layout = mock_Layout
    mock_go.Scatter = mock_Scatter
    mock.seal(mock_go)

    with mock.patch("wily.commands.graph.plotly.offline", mock_offline), mock.patch(
        "wily.commands.graph.go", mock_go
    ), mock.patch("wily.commands.graph.State", mock_State):
        graph(
            config=mock_config,
            path=path,
            metrics=metrics,
            output=output,
            x_axis=None,
            changes=False,
            aggregate=False,
        )

    mock_offline.plot.assert_called_once_with(
        {"data": [mock_scatter], "layout": mock_layout},
        auto_open=True,
        filename="wily-report.html",
        include_plotlyjs=True,
    )
    mock_Layout.assert_called_once_with(**LAYOUT_EXPECTED_ALL)
    mock_go.Scatter.assert_called_once_with(**SCATTER_EXPECTED_ALL)
    mock_State.assert_called_once_with(mock_config)


def test_metric_parts():
    result = metric_parts("raw.loc")
    assert result[0] == "raw"
    assert result[1] == "loc"


def test_metric_parts_no_operator():
    result = metric_parts("loc")
    assert result[0] == "raw"
    assert result[1] == "loc"


def test_metric_parts_no_metric():
    raised = False
    try:
        metric_parts("raw")
    except ValueError:
        raised = True
    assert raised, "metric_parts didn't raise ValueError for missing metric."


def test_metric_parts_invalid_metric():
    raised = False
    try:
        metric_parts("raw.blah")
    except ValueError:
        raised = True
    assert raised, "metric_parts didn't raise ValueError for invalid metric."

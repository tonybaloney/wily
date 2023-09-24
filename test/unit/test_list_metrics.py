"""Unit tests for the list_metrics command."""

from statistics import mean
from unittest import mock

from wily.commands.list_metrics import list_metrics

func_len = len(str(mean))

EXPECTED = """
cyclomatic operator:
╒════════════╤═══════════════════════╤════════╤═══════════════════╤═════════════╕
│ Name       │ Description           │ Type   │ Measure           │ Aggregate   │
╞════════════╪═══════════════════════╪════════╪═══════════════════╪═════════════╡
│ complexity │ Cyclomatic Complexity │ float  │ MetricType.AimLow │ mean        │
╘════════════╧═══════════════════════╧════════╧═══════════════════╧═════════════╛
maintainability operator:
╒════════╤═════════════════════════╤════════╤══════════════════════════╤═════════════╕
│ Name   │ Description             │ Type   │ Measure                  │ Aggregate   │
╞════════╪═════════════════════════╪════════╪══════════════════════════╪═════════════╡
│ rank   │ Maintainability Ranking │ str    │ MetricType.Informational │ mode        │
├────────┼─────────────────────────┼────────┼──────────────────────────┼─────────────┤
│ mi     │ Maintainability Index   │ float  │ MetricType.AimHigh       │ mean        │
╘════════╧═════════════════════════╧════════╧══════════════════════════╧═════════════╛
raw operator:
╒═════════════════╤══════════════════════╤════════╤══════════════════════════╤═════════════╕
│ Name            │ Description          │ Type   │ Measure                  │ Aggregate   │
╞═════════════════╪══════════════════════╪════════╪══════════════════════════╪═════════════╡
│ loc             │ Lines of Code        │ int    │ MetricType.Informational │ sum         │
├─────────────────┼──────────────────────┼────────┼──────────────────────────┼─────────────┤
│ lloc            │ L Lines of Code      │ int    │ MetricType.AimLow        │ sum         │
├─────────────────┼──────────────────────┼────────┼──────────────────────────┼─────────────┤
│ sloc            │ S Lines of Code      │ int    │ MetricType.AimLow        │ sum         │
├─────────────────┼──────────────────────┼────────┼──────────────────────────┼─────────────┤
│ comments        │ Multi-line comments  │ int    │ MetricType.AimHigh       │ sum         │
├─────────────────┼──────────────────────┼────────┼──────────────────────────┼─────────────┤
│ multi           │ Multi lines          │ int    │ MetricType.Informational │ sum         │
├─────────────────┼──────────────────────┼────────┼──────────────────────────┼─────────────┤
│ blank           │ blank lines          │ int    │ MetricType.Informational │ sum         │
├─────────────────┼──────────────────────┼────────┼──────────────────────────┼─────────────┤
│ single_comments │ Single comment lines │ int    │ MetricType.Informational │ sum         │
╘═════════════════╧══════════════════════╧════════╧══════════════════════════╧═════════════╛
halstead operator:
╒════════════╤═════════════════════════════╤════════╤═══════════════════╤═════════════╕
│ Name       │ Description                 │ Type   │ Measure           │ Aggregate   │
╞════════════╪═════════════════════════════╪════════╪═══════════════════╪═════════════╡
│ h1         │ Unique Operands             │ int    │ MetricType.AimLow │ sum         │
├────────────┼─────────────────────────────┼────────┼───────────────────┼─────────────┤
│ h2         │ Unique Operators            │ int    │ MetricType.AimLow │ sum         │
├────────────┼─────────────────────────────┼────────┼───────────────────┼─────────────┤
│ N1         │ Number of Operands          │ int    │ MetricType.AimLow │ sum         │
├────────────┼─────────────────────────────┼────────┼───────────────────┼─────────────┤
│ N2         │ Number of Operators         │ int    │ MetricType.AimLow │ sum         │
├────────────┼─────────────────────────────┼────────┼───────────────────┼─────────────┤
│ vocabulary │ Unique vocabulary (h1 + h2) │ int    │ MetricType.AimLow │ sum         │
├────────────┼─────────────────────────────┼────────┼───────────────────┼─────────────┤
│ length     │ Length of application       │ int    │ MetricType.AimLow │ sum         │
├────────────┼─────────────────────────────┼────────┼───────────────────┼─────────────┤
│ volume     │ Code volume                 │ float  │ MetricType.AimLow │ sum         │
├────────────┼─────────────────────────────┼────────┼───────────────────┼─────────────┤
│ difficulty │ Difficulty                  │ float  │ MetricType.AimLow │ sum         │
├────────────┼─────────────────────────────┼────────┼───────────────────┼─────────────┤
│ effort     │ Effort                      │ float  │ MetricType.AimLow │ sum         │
╘════════════╧═════════════════════════════╧════════╧═══════════════════╧═════════════╛
"""
EXPECTED = EXPECTED[1:]


def test_list_metrics_no_wrap(capsys):
    list_metrics(wrap=False)
    captured = capsys.readouterr()
    assert captured.out == EXPECTED


EXPECTED_WRAPPED = """
cyclomatic operator:
╒════════════╤═══════════════╤════════╤════════════════╤═════════════╕
│ Name       │ Description   │ Type   │ Measure        │ Aggregate   │
╞════════════╪═══════════════╪════════╪════════════════╪═════════════╡
│ complexity │ Cyclomatic    │ float  │ MetricType.Aim │ mean        │
│            │ Complexity    │        │ Low            │             │
╘════════════╧═══════════════╧════════╧════════════════╧═════════════╛
maintainability operator:
╒════════╤════════════════╤════════╤════════════════╤═════════════╕
│ Name   │ Description    │ Type   │ Measure        │ Aggregate   │
╞════════╪════════════════╪════════╪════════════════╪═════════════╡
│ rank   │ Maintainabilit │ str    │ MetricType.Inf │ mode        │
│        │ y Ranking      │        │ ormational     │             │
├────────┼────────────────┼────────┼────────────────┼─────────────┤
│ mi     │ Maintainabilit │ float  │ MetricType.Aim │ mean        │
│        │ y Index        │        │ High           │             │
╘════════╧════════════════╧════════╧════════════════╧═════════════╛
raw operator:
╒════════════════╤════════════════╤════════╤════════════════╤═════════════╕
│ Name           │ Description    │ Type   │ Measure        │ Aggregate   │
╞════════════════╪════════════════╪════════╪════════════════╪═════════════╡
│ loc            │ Lines of Code  │ int    │ MetricType.Inf │ sum         │
│                │                │        │ ormational     │             │
├────────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ lloc           │ L Lines of     │ int    │ MetricType.Aim │ sum         │
│                │ Code           │        │ Low            │             │
├────────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ sloc           │ S Lines of     │ int    │ MetricType.Aim │ sum         │
│                │ Code           │        │ Low            │             │
├────────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ comments       │ Multi-line     │ int    │ MetricType.Aim │ sum         │
│                │ comments       │        │ High           │             │
├────────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ multi          │ Multi lines    │ int    │ MetricType.Inf │ sum         │
│                │                │        │ ormational     │             │
├────────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ blank          │ blank lines    │ int    │ MetricType.Inf │ sum         │
│                │                │        │ ormational     │             │
├────────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ single_comment │ Single comment │ int    │ MetricType.Inf │ sum         │
│ s              │ lines          │        │ ormational     │             │
╘════════════════╧════════════════╧════════╧════════════════╧═════════════╛
halstead operator:
╒════════════╤════════════════╤════════╤════════════════╤═════════════╕
│ Name       │ Description    │ Type   │ Measure        │ Aggregate   │
╞════════════╪════════════════╪════════╪════════════════╪═════════════╡
│ h1         │ Unique         │ int    │ MetricType.Aim │ sum         │
│            │ Operands       │        │ Low            │             │
├────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ h2         │ Unique         │ int    │ MetricType.Aim │ sum         │
│            │ Operators      │        │ Low            │             │
├────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ N1         │ Number of      │ int    │ MetricType.Aim │ sum         │
│            │ Operands       │        │ Low            │             │
├────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ N2         │ Number of      │ int    │ MetricType.Aim │ sum         │
│            │ Operators      │        │ Low            │             │
├────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ vocabulary │ Unique         │ int    │ MetricType.Aim │ sum         │
│            │ vocabulary (h1 │        │ Low            │             │
│            │ + h2)          │        │                │             │
├────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ length     │ Length of      │ int    │ MetricType.Aim │ sum         │
│            │ application    │        │ Low            │             │
├────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ volume     │ Code volume    │ float  │ MetricType.Aim │ sum         │
│            │                │        │ Low            │             │
├────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ difficulty │ Difficulty     │ float  │ MetricType.Aim │ sum         │
│            │                │        │ Low            │             │
├────────────┼────────────────┼────────┼────────────────┼─────────────┤
│ effort     │ Effort         │ float  │ MetricType.Aim │ sum         │
│            │                │        │ Low            │             │
╘════════════╧════════════════╧════════╧════════════════╧═════════════╛
"""
EXPECTED_WRAPPED = EXPECTED_WRAPPED[1:]


def test_list_metrics_wrapped(capsys):
    mock_get_terminal_size = mock.Mock(return_value=(85, 24))
    mock_shutil = mock.Mock(get_terminal_size=mock_get_terminal_size)

    with mock.patch("wily.helper.shutil", mock_shutil):
        list_metrics(wrap=True)
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == EXPECTED_WRAPPED

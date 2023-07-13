"""Unit tests for the index command."""

from io import StringIO
from statistics import mean
from unittest import mock

from wily.commands.list_metrics import list_metrics
from wily.operators.maintainability import mode

EXPECTED = f"""
cyclomatic operator:
╒════════════╤═══════════════════════╤═════════════════╤═══════════════════╤═══════════════════════════════════════╕
│            │                       │ Name            │ Description       │ Type                                  │
╞════════════╪═══════════════════════╪═════════════════╪═══════════════════╪═══════════════════════════════════════╡
│ complexity │ Cyclomatic Complexity │ <class 'float'> │ MetricType.AimLow │ {mean} │
╘════════════╧═══════════════════════╧═════════════════╧═══════════════════╧═══════════════════════════════════════╛
maintainability operator:
╒══════╤═════════════════════════╤═════════════════╤══════════════════════════╤═══════════════════════════════════════╕
│      │                         │ Name            │ Description              │ Type                                  │
╞══════╪═════════════════════════╪═════════════════╪══════════════════════════╪═══════════════════════════════════════╡
│ rank │ Maintainability Ranking │ <class 'str'>   │ MetricType.Informational │ {mode} │
├──────┼─────────────────────────┼─────────────────┼──────────────────────────┼───────────────────────────────────────┤
│ mi   │ Maintainability Index   │ <class 'float'> │ MetricType.AimHigh       │ {mean} │
╘══════╧═════════════════════════╧═════════════════╧══════════════════════════╧═══════════════════════════════════════╛
raw operator:
╒═════════════════╤══════════════════════╤═══════════════╤══════════════════════════╤═════════════════════════╕
│                 │                      │ Name          │ Description              │ Type                    │
╞═════════════════╪══════════════════════╪═══════════════╪══════════════════════════╪═════════════════════════╡
│ loc             │ Lines of Code        │ <class 'int'> │ MetricType.Informational │ <built-in function sum> │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┼─────────────────────────┤
│ lloc            │ L Lines of Code      │ <class 'int'> │ MetricType.AimLow        │ <built-in function sum> │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┼─────────────────────────┤
│ sloc            │ S Lines of Code      │ <class 'int'> │ MetricType.AimLow        │ <built-in function sum> │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┼─────────────────────────┤
│ comments        │ Multi-line comments  │ <class 'int'> │ MetricType.AimHigh       │ <built-in function sum> │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┼─────────────────────────┤
│ multi           │ Multi lines          │ <class 'int'> │ MetricType.Informational │ <built-in function sum> │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┼─────────────────────────┤
│ blank           │ blank lines          │ <class 'int'> │ MetricType.Informational │ <built-in function sum> │
├─────────────────┼──────────────────────┼───────────────┼──────────────────────────┼─────────────────────────┤
│ single_comments │ Single comment lines │ <class 'int'> │ MetricType.Informational │ <built-in function sum> │
╘═════════════════╧══════════════════════╧═══════════════╧══════════════════════════╧═════════════════════════╛
halstead operator:
╒════════════╤═════════════════════════════╤═════════════════╤═══════════════════╤═════════════════════════╕
│            │                             │ Name            │ Description       │ Type                    │
╞════════════╪═════════════════════════════╪═════════════════╪═══════════════════╪═════════════════════════╡
│ h1         │ Unique Operands             │ <class 'int'>   │ MetricType.AimLow │ <built-in function sum> │
├────────────┼─────────────────────────────┼─────────────────┼───────────────────┼─────────────────────────┤
│ h2         │ Unique Operators            │ <class 'int'>   │ MetricType.AimLow │ <built-in function sum> │
├────────────┼─────────────────────────────┼─────────────────┼───────────────────┼─────────────────────────┤
│ N1         │ Number of Operands          │ <class 'int'>   │ MetricType.AimLow │ <built-in function sum> │
├────────────┼─────────────────────────────┼─────────────────┼───────────────────┼─────────────────────────┤
│ N2         │ Number of Operators         │ <class 'int'>   │ MetricType.AimLow │ <built-in function sum> │
├────────────┼─────────────────────────────┼─────────────────┼───────────────────┼─────────────────────────┤
│ vocabulary │ Unique vocabulary (h1 + h2) │ <class 'int'>   │ MetricType.AimLow │ <built-in function sum> │
├────────────┼─────────────────────────────┼─────────────────┼───────────────────┼─────────────────────────┤
│ length     │ Length of application       │ <class 'int'>   │ MetricType.AimLow │ <built-in function sum> │
├────────────┼─────────────────────────────┼─────────────────┼───────────────────┼─────────────────────────┤
│ volume     │ Code volume                 │ <class 'float'> │ MetricType.AimLow │ <built-in function sum> │
├────────────┼─────────────────────────────┼─────────────────┼───────────────────┼─────────────────────────┤
│ difficulty │ Difficulty                  │ <class 'float'> │ MetricType.AimLow │ <built-in function sum> │
├────────────┼─────────────────────────────┼─────────────────┼───────────────────┼─────────────────────────┤
│ effort     │ Effort                      │ <class 'float'> │ MetricType.AimLow │ <built-in function sum> │
╘════════════╧═════════════════════════════╧═════════════════╧═══════════════════╧═════════════════════════╛
"""
EXPECTED = EXPECTED[1:]


def test_list_metrics():
    stdout = StringIO()

    with mock.patch("sys.stdout", stdout):
        list_metrics()

    assert stdout.getvalue() == EXPECTED

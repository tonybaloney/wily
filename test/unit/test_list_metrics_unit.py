"""Unit tests for the list_metrics command."""

from statistics import mean
from unittest import mock

from wily.commands.list_metrics import list_metrics
from wily.operators.maintainability import mode

func_len = len(str(mean))

EXPECTED = f"""
cyclomatic operator:
╒════════════╤═══════════════════════╤═════════════════╤═══════════════════╤═{"═" * func_len}═╕
│ Name       │ Description           │ Type            │ Measure           │ Aggregate{" " * (func_len - 8)}│
╞════════════╪═══════════════════════╪═════════════════╪═══════════════════╪═{"═" * func_len}═╡
│ complexity │ Cyclomatic Complexity │ <class 'float'> │ MetricType.AimLow │ {mean} │
╘════════════╧═══════════════════════╧═════════════════╧═══════════════════╧═{"═" * func_len}═╛
maintainability operator:
╒════════╤═════════════════════════╤═════════════════╤══════════════════════════╤═{"═" * func_len}═╕
│ Name   │ Description             │ Type            │ Measure                  │ Aggregate{" " * (func_len - 8)}│
╞════════╪═════════════════════════╪═════════════════╪══════════════════════════╪═{"═" * func_len}═╡
│ rank   │ Maintainability Ranking │ <class 'str'>   │ MetricType.Informational │ {mode} │
├────────┼─────────────────────────┼─────────────────┼──────────────────────────┼─{"─" * func_len}─┤
│ mi     │ Maintainability Index   │ <class 'float'> │ MetricType.AimHigh       │ {mean} │
╘════════╧═════════════════════════╧═════════════════╧══════════════════════════╧═{"═" * func_len}═╛
raw operator:
╒═════════════════╤══════════════════════╤═══════════════╤══════════════════════════╤═════════════════════════╕
│ Name            │ Description          │ Type          │ Measure                  │ Aggregate               │
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
│ Name       │ Description                 │ Type            │ Measure           │ Aggregate               │
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


def test_list_metrics(capsys):

    list_metrics(wrap=False)
    captured = capsys.readouterr()
    assert captured.out == EXPECTED


EXPECTED_WRAPPED = f"""
cyclomatic operator:
╒════════════╤═══════════════╤══════════╤════════════════╤════════════════╕
│ Name       │ Description   │ Type     │ Measure        │ Aggregate      │
╞════════════╪═══════════════╪══════════╪════════════════╪════════════════╡
│ complexity │ Cyclomatic    │ <class   │ MetricType.Aim │ {str(mean)[:15]}│
│            │ Complexity    │ 'float'> │ Low            │ {str(mean)[15:29]} │
│            │               │          │                │ {str(mean)[29:]:<15}│
╘════════════╧═══════════════╧══════════╧════════════════╧════════════════╛
maintainability operator:
╒════════╤════════════════╤═══════════════╤════════════════╤════════════════╕
│ Name   │ Description    │ Type          │ Measure        │ Aggregate      │
╞════════╪════════════════╪═══════════════╪════════════════╪════════════════╡
│ rank   │ Maintainabilit │ <class 'str'> │ MetricType.Inf │ {str(mode)[:15]}│
│        │ y Ranking      │               │ ormational     │ {str(mode)[15:29]} │
│        │                │               │                │ {str(mode)[29:]:<15}│
├────────┼────────────────┼───────────────┼────────────────┼────────────────┤
│ mi     │ Maintainabilit │ <class        │ MetricType.Aim │ {str(mean)[:15]}│
│        │ y Index        │ 'float'>      │ High           │ {str(mean)[15:29]} │
│        │                │               │                │ {str(mean)[29:]:<15}│
╘════════╧════════════════╧═══════════════╧════════════════╧════════════════╛
raw operator:
╒════════════════╤════════════════╤═══════════════╤════════════════╤═══════════════╕
│ Name           │ Description    │ Type          │ Measure        │ Aggregate     │
╞════════════════╪════════════════╪═══════════════╪════════════════╪═══════════════╡
│ loc            │ Lines of Code  │ <class 'int'> │ MetricType.Inf │ <built-in     │
│                │                │               │ ormational     │ function sum> │
├────────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ lloc           │ L Lines of     │ <class 'int'> │ MetricType.Aim │ <built-in     │
│                │ Code           │               │ Low            │ function sum> │
├────────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ sloc           │ S Lines of     │ <class 'int'> │ MetricType.Aim │ <built-in     │
│                │ Code           │               │ Low            │ function sum> │
├────────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ comments       │ Multi-line     │ <class 'int'> │ MetricType.Aim │ <built-in     │
│                │ comments       │               │ High           │ function sum> │
├────────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ multi          │ Multi lines    │ <class 'int'> │ MetricType.Inf │ <built-in     │
│                │                │               │ ormational     │ function sum> │
├────────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ blank          │ blank lines    │ <class 'int'> │ MetricType.Inf │ <built-in     │
│                │                │               │ ormational     │ function sum> │
├────────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ single_comment │ Single comment │ <class 'int'> │ MetricType.Inf │ <built-in     │
│ s              │ lines          │               │ ormational     │ function sum> │
╘════════════════╧════════════════╧═══════════════╧════════════════╧═══════════════╛
halstead operator:
╒════════════╤════════════════╤═══════════════╤════════════════╤═══════════════╕
│ Name       │ Description    │ Type          │ Measure        │ Aggregate     │
╞════════════╪════════════════╪═══════════════╪════════════════╪═══════════════╡
│ h1         │ Unique         │ <class 'int'> │ MetricType.Aim │ <built-in     │
│            │ Operands       │               │ Low            │ function sum> │
├────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ h2         │ Unique         │ <class 'int'> │ MetricType.Aim │ <built-in     │
│            │ Operators      │               │ Low            │ function sum> │
├────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ N1         │ Number of      │ <class 'int'> │ MetricType.Aim │ <built-in     │
│            │ Operands       │               │ Low            │ function sum> │
├────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ N2         │ Number of      │ <class 'int'> │ MetricType.Aim │ <built-in     │
│            │ Operators      │               │ Low            │ function sum> │
├────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ vocabulary │ Unique         │ <class 'int'> │ MetricType.Aim │ <built-in     │
│            │ vocabulary (h1 │               │ Low            │ function sum> │
│            │ + h2)          │               │                │               │
├────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ length     │ Length of      │ <class 'int'> │ MetricType.Aim │ <built-in     │
│            │ application    │               │ Low            │ function sum> │
├────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ volume     │ Code volume    │ <class        │ MetricType.Aim │ <built-in     │
│            │                │ 'float'>      │ Low            │ function sum> │
├────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ difficulty │ Difficulty     │ <class        │ MetricType.Aim │ <built-in     │
│            │                │ 'float'>      │ Low            │ function sum> │
├────────────┼────────────────┼───────────────┼────────────────┼───────────────┤
│ effort     │ Effort         │ <class        │ MetricType.Aim │ <built-in     │
│            │                │ 'float'>      │ Low            │ function sum> │
╘════════════╧════════════════╧═══════════════╧════════════════╧═══════════════╛
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

import pytest

import wily.operators


def test_resolve_operator():
    op = wily.operators.resolve_operator("cyclomatic")
    assert op == wily.operators.OPERATOR_CYCLOMATIC


def test_resolve_bad_operator():
    with pytest.raises(ValueError):
        wily.operators.resolve_operator("banana")


def test_resolve_operators():
    ops = wily.operators.resolve_operators(("cyclomatic", "raw"))
    assert ops[0] == wily.operators.OPERATOR_CYCLOMATIC
    assert ops[1] == wily.operators.OPERATOR_RAW


def test_resolve_metric():
    metric = wily.operators.resolve_metric("raw.loc")
    assert metric.name == "loc"


def test_resolve_invalid_metric():
    with pytest.raises(ValueError):
        wily.operators.resolve_metric("raw.spanner")


def test_resolve_short_metric():
    metric = wily.operators.resolve_metric("loc")
    assert metric.name == "loc"

from pathlib import PosixPath

import pytest

from wily.commands.rank import aggregate_metric


def test_aggregate_metric():
    # given
    data = [
        (
            PosixPath("wily/config.py"),
            "27a96be",
            "an author",
            "2019-01-15",
            "82.41669266978485",
        ),
        (
            PosixPath("wily/cache.py"),
            "27a96be",
            "an author",
            "2019-01-15",
            "82.41669266978485",
        ),
    ]
    expected = ["Total", "---", "---", "---", 164.8333853395697]

    # when
    actual = aggregate_metric(data)

    # then
    assert actual == expected


def test_aggregate_metric_empty():
    # given
    data = []
    expected = ["Total", "---", "---", "---", 0]

    # when
    actual = aggregate_metric(data)

    # then
    assert actual == expected

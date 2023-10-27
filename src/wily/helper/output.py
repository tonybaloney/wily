"""Output helpers for wily."""
import json
from collections.abc import Sequence


def print_json(data: Sequence, headers: Sequence, path: str = ""):
    """
    Print data as JSON.

    :param data: Rows of data to print

    :param headers: Headers of data to print

    :param path: The path to the file
    """
    json_data = [{headers[x]: d[x] for x in range(len(headers))} for d in data]
    if path:
        for entry in json_data:
            entry["Filename"] = path
    print(json.dumps(json_data, indent=2))

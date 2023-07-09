"""Output helpers for wily."""
import json

import tabulate


def print_result(as_json, data, headers, table_format, path=""):
    """
    Print data as tabulate table or JSON.

    :param as_json: Whether to print as JSON
    :type as_json: ``bool``

    :param data: Rows of data to print
    :type data: ``list``

    :param headers: Headers of data to print
    :type headers: ``tuple``

    :param table_format: Grid format style for tabulate
    :type table_format: ``str``

    :param path: The path to the file
    :type  path: ``str``
    """
    if as_json:
        json_data = [{headers[x]: d[x] for x in range(len(headers))} for d in data]
        if path:
            for entry in json_data:
                entry["Filename"] = path
        print(json.dumps(json_data, indent=2))
    else:
        print(
            tabulate.tabulate(headers=headers, tabular_data=data, tablefmt=table_format)
        )

"""
A module including decorators for wily.

This API is not intended to be public and should not be consumed directly.

"""

from wily import __version__


def add_version(f):
    """
    Add the version of wily to the help heading.

    :param f: function to decorate
    :return: decorated function
    """
    doc = f.__doc__
    f.__doc__ = "Version: " + __version__ + "\n\n" + doc
    return f

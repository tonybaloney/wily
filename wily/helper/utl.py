"""
Miscelaionus utility methods for wily

MODULE:3-2
"""
import setuptools
import pkgutil
import pathlib

WILY_ROOT = pathlib.Path(__file__).joinpath("..", "..").resolve()


def collect_wily_modules():
    """
    Return all wiley modules.
    """
    wily_modules = set()
    for pkg in setuptools.find_packages():
        pkg_path = f"{WILY_ROOT.parent}/{pkg.replace('.', '/')}"
        for _, name, ispkg in pkgutil.iter_modules([pkg_path]):
            if not ispkg:
                wily_modules.add(f"{pkg}.{name}")
    return wily_modules


if __name__ == "__main__":
    pytes.main("")

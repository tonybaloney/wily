from importlib import import_module
import pytest
from wily.helper.utl import collect_wily_modules

WILEY_MODULES = ("module_name", collect_wily_modules())


@pytest.mark.parametrize(*WILEY_MODULES)
def test_modules(module_name):
    """
    Test the every module has a module number
    """
    docstr = import_module(module_name).__doc__
    module_line = docstr.splitlines()[-1]
    print(module_name)
    print(module_line)
    assert module_line.startswith("MODULE:")


if __name__ == "__main__":
    pytest.main(args=["-v"])

from collections import namedtuple
from .mccabe import MccabeOperator


"""Type for an operator"""
Operator = namedtuple("Operator", "name cls description")


"""Mccabe Operator defined in `wily.operators.mccabe`"""
OPERATOR_MCCABE = Operator(name="mccabe", cls=MccabeOperator, description="Number of branches via the Mccabe algorithm")


"""Set of all available operators"""
ALL_OPERATORS = {
    OPERATOR_MCCABE
}


class BaseOperator(object):
    """Abstract Operator Class"""
    def run(self, module, options):
        raise NotImplementedError()

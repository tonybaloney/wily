from collections import namedtuple


class BaseOperator(object):
    """Abstract Operator Class"""
    def run(self, module, options):
        raise NotImplementedError()


from wily.operators.mccabe import MccabeOperator


"""Type for an operator"""
Operator = namedtuple("Operator", "name cls description")


"""Mccabe Operator defined in `wily.operators.mccabe`"""
OPERATOR_MCCABE = Operator(name="mccabe", cls=MccabeOperator, description="Number of branches via the Mccabe algorithm")


"""Set of all available operators"""
ALL_OPERATORS = {
    OPERATOR_MCCABE
}


def resolve_operator(name):
    """
    Get the :namedtuple:`wily.operators.Operator` for a given name
    :param name: The name of the operator
    :return: The operator type
    """
    r = [operator for operator in ALL_OPERATORS if operator.name == name.lower()]
    if not r:
        raise ValueError(f"Operator {name} not recognised.")
    else:
        return r[0]


def resolve_operators(operators):
    return [resolve_operator(operator) for operator in operators]




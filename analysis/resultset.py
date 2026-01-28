from parsing.expressions.scalar_expression import ScalarExpression, AliasedScalarIdentifierExpression
from typing import Protocol

class ResultSet(Protocol):

    def columns(self) -> list[ScalarExpression | AliasedScalarIdentifierExpression]:
        pass

    def trace_column(self, column: ScalarExpression | AliasedScalarIdentifierExpression):
        pass

    def predicate() -> ScalarExpression:
        pass
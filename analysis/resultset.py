from typing import Protocol
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from parsing.expressions.scalar_expression import ScalarExpression

class ResultSet(Protocol):

    def columns(self) -> list:
        pass

    def trace_column(self, column: 'ScalarExpression'):
        pass

    def predicate() -> 'ScalarExpression':
        pass
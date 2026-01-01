from __future__ import annotations
from typing import TYPE_CHECKING
from parsing.expressions.clause import Clause
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token

if TYPE_CHECKING:
    from parsing.expressions.scalar_expression import ScalarExpression

class VariableAssignmentExpression(Clause):

    def __init__(self, var: TokenContext, equals: TokenContext, val: ScalarExpression):
        super().__init__([var, equals, val])
        self.var = var
        self.val = val

    @staticmethod
    def consume(reader: Reader):
        from parsing.expressions.scalar_expression import ScalarExpression
        return VariableAssignmentExpression(
            reader.expect(Token.VARIABLE),
            reader.expect_symbol('='),
            ScalarExpression.consume(reader)
        )
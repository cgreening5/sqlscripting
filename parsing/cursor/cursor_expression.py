from parsing.expressions.clause import Clause
from parsing.expressions.select_expression import SelectExpression
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token


class CursorExpression(Clause):

    def __init__(
            self,
            declare: TokenContext,
            cursor_name: TokenContext,
            _as: TokenContext,
            cursor: TokenContext,
            _for: TokenContext,
            select: SelectExpression
        ):
        super().__init__([
            declare,
            cursor_name,
            _as,
            cursor,
            _for,
            select,
        ])
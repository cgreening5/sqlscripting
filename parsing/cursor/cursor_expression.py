from typing import Self
from parsing.expressions.clause import Clause
from parsing.expressions.select_expression import SelectExpression
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token

class FetchExpression(Clause):

    def __init__(self, fetch: TokenContext, cursor: TokenContext, into: TokenContext, variables: list[TokenContext]):
        super().__init__([fetch, cursor, into] + variables)
        self.cursor = cursor
        self.variables = variables

    @staticmethod
    def consume(reader: Reader):
        fetch = reader.expect_word('fetch')
        cursor = reader.expect_any_of([Token.VARIABLE, Token.WORD])
        into = reader.expect_word('into')
        variables = []
        while True:
            variables.append(reader.expect(Token.VARIABLE))
            if reader.curr_value_lower == ',':
                variables.append(reader.expect_symbol(','))
            else:
                break
        return FetchExpression(fetch, cursor, into, variables)

class OpenExpression(Clause):

    def __init__(self, open: TokenContext, cursor: TokenContext):
        super().__init__([open, cursor])
        self.cursor = cursor

    @staticmethod
    def consume(reader: Reader) -> Self:
        return OpenExpression(
            reader.expect_word('open'),
            reader.expect_any_of([Token.WORD, Token.QUOTED_IDENTIFIER])
        )

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
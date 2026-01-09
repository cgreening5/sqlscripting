from typing import Self
from parsing.expressions.clause import Clause
from parsing.expressions.select_expression import SelectExpression
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token

class FetchExpression(Clause):

    def __init__(self, fetch: TokenContext, _next: TokenContext, _from: TokenContext, cursor: TokenContext, into: TokenContext, variables: list[TokenContext]):
        super().__init__([fetch, _next, _from, cursor, into, *variables])
        self.cursor = cursor
        self.next = _next
        self.variables = variables

    def uppercase(self):
        return ''.join([
            str(token) if token == self.cursor else token.uppercase() for token in self.tokens if token
        ])

    @staticmethod
    def consume(reader: Reader):
        fetch = reader.expect_word('fetch')
        # todo: there are a couple more harder ones
        if reader.curr_value_lower in [
            'next',
            'prior',
            'first',
            'last',
        ]:
            _next = reader.expect_word()
            _from = reader.expect_word('from')
        else:
            _next = None
            _from = reader.consume_optional_word('from')
        cursor = reader.expect_any_of([Token.VARIABLE, Token.WORD])
        into = reader.expect_word('into')
        variables = []
        while True:
            variables.append(reader.expect(Token.VARIABLE))
            if reader.curr_value_lower == ',':
                variables.append(reader.expect_symbol(','))
            else:
                break
        return FetchExpression(fetch, _next, _from, cursor, into, variables)

    def uppercase(self):
        return ''.join([
            str(token) if token == self.cursor else token.uppercase() for token in self.tokens if token
        ])

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
    
    def uppercase(self):
        return ''.join([
            str(token) if token == self.cursor else token.uppercase() for token in self.tokens if token
        ])

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
        self.cursor_name = cursor_name

    def uppercase(self):
        return ''.join([
            str(token) if token == self.cursor_name else token.uppercase() for token in self.tokens if token
        ])

class CloseCursorExpression(Clause):

    def __init__(self, close, cursor):
        super().__init__([close, cursor])
        self.cursor = cursor

    @staticmethod
    def consume(reader: Reader):
        close = reader.expect_keyword('close')
        cursor = reader.expect_any_of([Token.WORD, Token.QUOTED_IDENTIFIER])
        return CloseCursorExpression(close, cursor)
    
    def uppercase(self):
        return ''.join([
            str(token) if token == self.cursor else token.uppercase() for token in self.tokens if token
        ])

class DeallocateCursorExpression(Clause):

    def __init__(self, close, cursor):
        super().__init__([close, cursor])
        self.cursor = cursor

    @staticmethod
    def consume(reader: Reader):
        close = reader.expect_word('deallocate')
        cursor = reader.expect_any_of([Token.WORD, Token.QUOTED_IDENTIFIER])
        return DeallocateCursorExpression(close, cursor)
    
    def uppercase(self):
        return ''.join([
            str(token) if token == self.cursor else token.uppercase() for token in self.tokens if token
        ])
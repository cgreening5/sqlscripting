from parsing.expressions.clause import Clause
from parsing.expressions.scalar_expression import IdentifierExpression
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token


class UseExpression(Clause):
    def __init__(self, use: TokenContext, database: IdentifierExpression):
        super().__init__([use, database])
        self.use = use
        self.database = database

    @staticmethod
    def consume(reader: Reader) -> 'UseExpression':
        use = reader.expect_word('use')
        database = IdentifierExpression.consume(reader)
        return UseExpression(use, database)
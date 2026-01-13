from parsing.expressions.arguments_list import ArgumentsListExpression
from parsing.expressions.clause import Clause
from parsing.expressions.scalar_expression import IdentifierExpression
from parsing.expressions.select_expression import SelectExpression
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token

class InsertColumnsExpression(Clause):

    def __init__(self, opening_parenthesis, comma_separated_columns, closing_parenthesis):
        super().__init__([opening_parenthesis] + comma_separated_columns + [closing_parenthesis])
        self.columns = [
            token for i, token in enumerate(comma_separated_columns) if i % 2 == 0
        ]

    def uppercase(self):
        return ''.join(
            str(token) if token in self.columns else token.uppercase() for token in self.tokens
        )
    
    def lowercase(self):
        return ''.join(
            str(token) if token in self.columns else token.lowercase() for token in self.tokens
        )

    @staticmethod
    def consume(reader: Reader):
        opening_parenthesis = reader.expect_symbol('(')
        comma_separated_columns = []
        while True:
            comma_separated_columns.append(
                reader.expect_any_of([Token.WORD, Token.QUOTED_IDENTIFIER])
            )
            if reader.curr_value_lower == ')':
                return InsertColumnsExpression(
                    opening_parenthesis,
                    comma_separated_columns,
                    reader.expect_symbol(')')
                )
            comma_separated_columns.append(reader.expect_symbol(','))
                


class InsertExpression(Clause):

    def __init__(
            self,
            insert: TokenContext,
            into: TokenContext,
            table: TokenContext | IdentifierExpression,
            columns: InsertColumnsExpression,
            select: SelectExpression,
            values: TokenContext,
            arg_lists: list[ArgumentsListExpression],
        ):
        super().__init__([
            insert,
            into,
            table,
            columns,
            select,
            values,
            *(arg_lists or [])
        ])

    @staticmethod
    def consume(reader: Reader):
        insert = reader.expect_word('insert')
        into = reader.expect_word('into')
        if reader.curr.type == Token.VARIABLE:
            table = reader.expect(Token.VARIABLE)
        else:
            table = IdentifierExpression.consume(reader)
        if reader.curr_value_lower == '(':
            columns = InsertColumnsExpression.consume(reader)
        else:
            columns = None
        if reader.curr_value_lower == 'select':
            select = SelectExpression.consume(reader)
            values = None
            arg_lists = None
        elif reader.curr_value_lower == 'values':
            select = None
            values = reader.expect_word('values')
            arg_lists = []
            while True:
                arg_lists.append(ArgumentsListExpression.consume(reader))
                if reader.curr_value_lower == ',':
                    arg_lists.append(reader.expect_symbol(','))
                    arg_lists.append(ArgumentsListExpression.consume(reader))
                else:
                    break
        return InsertExpression(
            insert,
            into,
            table,
            columns,
            select,
            values,
            arg_lists
        )

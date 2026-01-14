from parsing.expressions.arguments_list import ArgumentsListExpression
from parsing.expressions.clause import Clause
from parsing.expressions.datatype import DataTypeClause
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token

class IdentityExpression(Clause):

    def __init__(self, identity: TokenContext, args: ArgumentsListExpression):
        super().__init__([identity, args])
        [self.initial, self.increment] = args.arguments

    @staticmethod
    def consume(reader: Reader):
        return IdentityExpression(
            reader.expect_word('identity'),
            ArgumentsListExpression.consume(reader)
        )
    
class PrimaryKeyExpression(Clause):

    def __init__(self, primary: TokenContext, key: TokenContext):
        super().__init__([primary, key])

    @staticmethod
    def consume(reader: Reader):
        return PrimaryKeyExpression(
            reader.expect_word('primary'),
            reader.expect_word('key')
        )

class NotNullExpression(Clause):
    
    def __init__(self, _not: TokenContext, null: TokenContext):
        super().__init__([_not, null])
    
    @staticmethod
    def consume(reader:Reader):
        return NotNullExpression(
            reader.expect_word('not'),
            reader.expect_word('null')
        )

class ColumnDefinitionExpression(Clause):

    def __init__(self, name: TokenContext, datatype: DataTypeClause, attributes: list[Clause]):
        super().__init__([name, datatype] + attributes)
        self.name = name
        if name.type == Token.WORD:
            name.type = Token.IDENTIFIER
        self.datatype = datatype
        self.attributes = attributes

    @staticmethod
    def consume(reader: Reader):
        name = reader.expect_any_of([Token.WORD, Token.QUOTED_IDENTIFIER])
        datatype = DataTypeClause.consume(reader)
        attributes = []
        while reader.curr_value_lower in [ 'identity', 'primary', 'not' ]:
            if reader.curr_value_lower == 'identity':
                attributes.append(IdentityExpression.consume(reader))
            elif reader.curr_value_lower == 'primary':
                attributes.append(PrimaryKeyExpression.consume(reader))
            elif reader.curr_value_lower == 'not':
                attributes.append(NotNullExpression.consume(reader))
        return ColumnDefinitionExpression(
            name, 
            datatype, 
            attributes
        )

class TableDefinitionExpression(Clause):

    def __init__(
        self,
        opening_parenthesis: TokenContext,
        comma_separated_column_definitions: list[TokenContext|Clause],
        closing_parenthesis: TokenContext
    ):
        super().__init__([
            opening_parenthesis, 
            *comma_separated_column_definitions, 
            closing_parenthesis
        ])
        self.columns = list(filter(lambda c: isinstance(c, ColumnDefinitionExpression), comma_separated_column_definitions))

    @staticmethod
    def consume(reader: Reader):
        columns = []
        opening_parenthesis = reader.expect_symbol('(')
        while True:
            columns.append(ColumnDefinitionExpression.consume(reader))
            if reader.curr_value_lower == ',':
                columns.append(reader.expect_symbol(','))
            else:
                return TableDefinitionExpression(
                    opening_parenthesis,
                    columns,
                    reader.expect_symbol(')')
                )
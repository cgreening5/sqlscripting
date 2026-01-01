from parsing.expressions.clause import Clause
from parsing.expressions.datatype import DataTypeClause
from parsing.expressions.token_context import TokenContext
from parsing.expressions.variable_assignment import VariableAssignmentExpression
from parsing.reader import Reader
from parsing.tokenizer import Token


class DeclareVariableExpression(Clause):
    def __init__(self, declare: TokenContext, variable: TokenContext, as_token: TokenContext, datatype: Clause, end_of_statement: list[Token]):
        super().__init__([declare, variable, as_token, datatype] + end_of_statement)
        self.declare = declare
        self.variable = variable
        self.datatype = datatype

    def __repr__(self):
        return f"DeclareClause(variable='{self.variable}', datatype='{self.datatype}')"

class DefineTableExpression(Clause):
    def __init__(self, open_paren: TokenContext, columns: list[tuple[TokenContext, Clause]], close_paren: TokenContext):
        tokens: list[TokenContext] = [open_paren]
        for column in columns:
            tokens.extend(column)
        tokens.append(close_paren)
        super().__init__(tokens)
        self.open_paren = open_paren
        self.columns = columns
        self.close_paren = close_paren

    def consume(reader: Reader):
        return reader.expect_word('')

class DeclareTableVariableExpression(Clause):
    def __init__(self, 
        declare: TokenContext,
        name: TokenContext, 
        as_token: TokenContext, 
        table: TokenContext, 
        table_definition: DefineTableExpression
    ):
        super().__init__([declare, name, as_token, table, table_definition])
        self.name = name
        self.table_definition = table_definition

    def __repr__(self):
        return f"DeclareTableVariableClause(variable='{self.variable}', table_definition={self.table_definition})"
    
class DeclareVariableExpression(Clause):
    def __init__(self, declare: TokenContext, variable: TokenContext, as_token: TokenContext, datatype: Clause):
        super().__init__([declare, variable, as_token, datatype])
        self.declare = declare
        self.variable = variable
        self.datatype = datatype

    @classmethod
    def consume(reader: Reader) -> Clause:
        declare = reader.expect_word('declare')
        variable = reader.expect(Token.VARIABLE)
        as_token = reader.consume_optional_word('as')

        if reader.curr.type == Token.WORD and reader.curr_value_lower == 'table':
            table = reader.expect_word('table')
            table_expression = DefineTableExpression.consume(reader)
            return DeclareTableVariableExpression(declare, variable, table, as_token, table_expression)
        else:
            datatype = DataTypeClause.consume(reader)
            return DeclareVariableExpression(declare, variable, as_token, datatype)

class VariableExpression(Clause):

    def __init__(self, var):
        super().__init__([var])
        self.var = var

    @staticmethod
    def consume(reader: Reader):
        return VariableExpression(reader.expect(Token.VARIABLE))

class SetExpression(Clause):

    def __init__(self, set, variable_assignment):
        super().__init__([set, variable_assignment])
        self.variable_assignment = variable_assignment

    @staticmethod
    def consume(reader: Reader):
        from parsing.expressions.scalar_expression import ScalarExpression
        return SetExpression(
            reader.expect_word('set'),
            VariableAssignmentExpression.consume(reader)
        )
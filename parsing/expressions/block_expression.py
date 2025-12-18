from parsing.expressions.clause import Clause
from parsing.expressions.datatype import DataTypeClause
from parsing.expressions.declare_expression import DeclareTableVariableExpression, DeclareVariableExpression, SetExpression
from parsing.expressions.insert_expression import InsertExpression
from parsing.expressions.select_expression import SelectExpression
from parsing.expressions.table_definition import TableDefinitionExpression
from parsing.expressions.token_context import TokenContext
from parsing.expressions.use_expression import UseExpression
from parsing.expressions.while_expression import WhileExpression
from parsing.reader import Reader
from parsing.tokenizer import Token


class BlockExpression(Clause):

    def __init__(self, expressions: list[Clause]):
        super().__init__(expressions)
        self.expressions = expressions

    @staticmethod
    def consume(reader: Reader):
        clauses: list[Clause|TokenContext] = []
        while not reader.eof and reader.curr_value_lower != 'end':
            if reader.curr.type in (Token.WHITESPACE, Token.NEWLINE):
                clauses.append(Clause([reader.read()]))
                continue
            elif reader.curr.type == Token.WORD:
                value = reader.curr_value_lower
                if value == 'use':
                    clauses.append(UseExpression.consume(reader))
                elif value == 'declare':
                    clauses.append(BlockExpression._consume_declare(reader))
                elif value == 'insert':
                    clauses.append(InsertExpression.consume(reader))
                elif value == 'select':
                    clauses.append(SelectExpression.consume(reader))
                elif value == 'begin':
                    clauses.append(BeginEndBlock.consume(reader))
                elif value == 'set':
                    clauses.append(SetExpression.consume(reader))
                elif value == 'while':
                    clauses.append(WhileExpression.consume(reader))
                else:
                    raise ValueError(f"Unexpected token '{reader.curr.__repr__()}'")
            else:
                raise ValueError(f"Unexpected token '{reader.curr.__repr__()}'")
            if reader.curr_value_lower == ';':
                clauses.append(reader.expect_symbol(';'))
        return clauses
    
    def _consume_declare(reader: Reader):
        declare = reader.expect_word('declare')
        variable = reader.expect(Token.VARIABLE)

        as_token = reader.consume_optional_word('as')
        if reader.curr.type == Token.WORD and reader.curr_value_lower == 'table':
            table = reader.expect_word('table')
            table_expression = TableDefinitionExpression.consume(reader)
            return DeclareTableVariableExpression(declare, variable, table, as_token, table_expression)
        else:
            datatype = DataTypeClause.consume(reader)
            return DeclareVariableExpression(declare, variable, as_token, datatype)

class BeginEndBlock(Clause):

    def __init__(self, begin: TokenContext, block: BlockExpression, end: TokenContext):
        super().__init__([begin, block, end])
        self.block = block

    @staticmethod
    def consume(reader: Reader):
        return BeginEndBlock(
            reader.expect_word('begin'),
            BlockExpression.consume(reader),
            reader.expect_word('end'),
        )
from parsing.cursor.cursor_expression import CloseCursorExpression, CursorExpression, DeallocateCursorExpression, FetchExpression, OpenExpression
from parsing.expressions.clause import Clause
from parsing.expressions.datatype import DataTypeClause
from parsing.expressions.declare_expression import DeclareTableVariableExpression, DeclareVariableExpression, SetExpression
from parsing.expressions.insert_expression import InsertExpression
from parsing.expressions.scalar_expression import BooleanExpression
from parsing.expressions.select_expression import SelectExpression
from parsing.expressions.table_definition import TableDefinitionExpression
from parsing.expressions.token_context import TokenContext
from parsing.expressions.transactions import BeginTransactionExpression, CommitTransactionExpression
from parsing.expressions.use_expression import UseExpression
from parsing.expressions.while_expression import WhileExpression
from parsing.reader import Reader
from parsing.tokenizer import Token
from parsing.update import UpdateExpression

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
            else:
                clauses.append(BlockExpression.consume_top_level_expression(reader))
            if reader.curr_value_lower == ';':
                clauses.append(reader.expect_symbol(';'))
        return BlockExpression(clauses)
    
    @staticmethod
    def consume_top_level_expression(reader: Reader):
        if reader.curr.type == Token.WORD:
            value = reader.curr_value_lower
            if value == 'use':
                return UseExpression.consume(reader)
            elif value == 'declare':
                return BlockExpression._consume_declare(reader)
            elif value == 'insert':
                return InsertExpression.consume(reader)
            elif value == 'select':
                return SelectExpression.consume(reader)
            elif value == 'begin':
                pos = reader._position
                reader.expect_word()
                if reader.curr_value_lower in ('tran', 'transaction'):
                    reader._position = pos
                    return BeginTransactionExpression.consume(reader)
                else:
                    reader._position = pos
                    return BeginEndBlock.consume(reader)
            elif value == 'commit':
                return CommitTransactionExpression.consume(reader)
            elif value == 'close':
                return CloseCursorExpression.consume(reader)
            elif value == 'deallocate':
                return DeallocateCursorExpression.consume(reader)
            elif value == 'set':
                return SetExpression.consume(reader)
            elif value == 'while':
                return WhileExpression.consume(reader)
            elif value == 'open':
                return OpenExpression.consume(reader)
            elif value == 'fetch':
                return FetchExpression.consume(reader)
            elif value == 'update':
                return UpdateExpression.consume(reader)
            elif value == 'if':
                return IfExpression.consume(reader)
            else:
                raise ValueError(f"Unexpected token '{reader.curr.__repr__()}'")
        else:
            raise ValueError(f"Unexpected token '{reader.curr.__repr__()}'")
    
    def _consume_declare(reader: Reader):
        declare = reader.expect_word('declare')
        variable = reader.expect_any_of([Token.VARIABLE, Token.WORD])

        as_token = reader.consume_optional_word('as')
        if reader.curr.type == Token.WORD and reader.curr_value_lower == 'table':
            table = reader.expect_word('table')
            table_expression = TableDefinitionExpression.consume(reader)
            return DeclareTableVariableExpression(declare, variable, as_token, table, table_expression)
        elif reader.curr_value_lower == 'cursor':
            return CursorExpression(
                declare,
                variable,
                as_token,
                reader.expect_word('cursor'),
                reader.expect_word('for'),
                SelectExpression.consume(reader)
            )
        else:
            datatype = DataTypeClause.consume(reader)
            return DeclareVariableExpression(declare, variable, as_token, datatype)

class IfExpression(Clause):

    def __init__(
            self, 
            _if: TokenContext, 
            condition: BooleanExpression,
            conditional_expression: Clause, 
            _else: TokenContext,
            else_expression: Clause
        ):
        super().__init__([_if, condition, conditional_expression, _else, else_expression])

    @staticmethod
    def consume(reader: Reader):
        _if = reader.expect_word('if')
        condition = BooleanExpression.consume(reader)
        conditional_expression = BlockExpression.consume_top_level_expression(reader)
        if reader.curr_value_lower == 'else':
            _else = reader.expect_word('else')
            else_expression = BlockExpression.consume_top_level_expression(reader)
        else:
            _else = None
            else_expression = None
        return IfExpression(_if, condition, conditional_expression, _else, else_expression)

            


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
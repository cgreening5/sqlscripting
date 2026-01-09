from __future__ import annotations
from typing import TYPE_CHECKING
from parsing.expressions.clause import Clause
from parsing.expressions.declare_expression import VariableExpression
from parsing.expressions.token_context import TokenContext
from parsing.expressions.variable_assignment import VariableAssignmentExpression
from parsing.reader import Reader
from parsing.tokenizer import Token

if TYPE_CHECKING:
    from parsing.expressions.scalar_expression import BooleanExpression, IdentifierExpression, ScalarExpression, AliasedIdentifierExpression

class SelectExpression(Clause):

    def __init__(
            self, 
            select: TokenContext,
            top: TokenContext,
            top_n: ScalarExpression,
            distinct: TokenContext | None,
            comma_separated_projection: list[ScalarExpression | TokenContext | VariableAssignmentExpression],
            _from: FromExpression,
            where: TokenContext,
            predicate: BooleanExpression,
        ):
        from parsing.expressions.scalar_expression import ScalarExpression
        super().__init__([
            select, 
            top, 
            top_n, 
            distinct, 
            *comma_separated_projection, 
            _from, 
            where, 
            predicate,
        ])
        self.top_n = top_n
        self.distinct = distinct
        self.projection = list(filter(lambda c: isinstance(c, ScalarExpression), comma_separated_projection))
        self._from = _from
        self.predicate = predicate

    @classmethod
    def consume(cls, reader: Reader):
        from parsing.expressions.scalar_expression import ScalarExpression, BooleanExpression
        select = reader.expect_word('select')
        top = reader.consume_optional_word('top')
        if top:
            top_n = ScalarExpression.consume(reader)
        else:
            top_n = None
        distinct = reader.consume_optional_word('distinct')
        comma_separated_projection = []
        while True:
            expression = ScalarExpression.consume(reader)
            if reader.curr_value_lower == 'as':
                expression = AliasedIdentifierExpression(
                    expression,
                    reader.expect_word('as'),
                    reader.expect_any_of([Token.QUOTED_IDENTIFIER, Token.WORD])
                )
            elif isinstance(expression, VariableExpression) and reader.curr_value_lower == '=':
                expression = VariableAssignmentExpression(
                    expression,
                    reader.expect_symbol('='),
                    ScalarExpression.consume(reader)
                )
            comma_separated_projection.append(expression)
            if reader.curr_value_lower == ',':
                comma_separated_projection.append(reader.expect_symbol(','))
            else:
                break
        _from = FromExpression.consume(reader)
        where = None
        predicate = None
        if reader.curr_value_lower == 'where':
            where = reader.expect_word('where')
            predicate = BooleanExpression.consume(reader)
        return SelectExpression(
            select, 
            top, top_n, 
            distinct, 
            comma_separated_projection, 
            _from,
            where, 
            predicate
        )
    
class JoinExpression(Clause):

    def __init__(
        self, 
        join_type: TokenContext, 
        join: TokenContext, 
        table: IdentifierExpression | AliasedIdentifierExpression,
        on: TokenContext, 
        condition: BooleanExpression
    ):
        super().__init__([join_type, join, table, on, condition])
        self.join_type =  join_type
        self.table = table
        self.condition = condition

    @staticmethod
    def consume(reader: Reader):
        from parsing.expressions.scalar_expression import BooleanExpression, IdentifierExpression, AliasedIdentifierExpression
        join_type = reader.consume_optional_word('left') \
            or reader.consume_optional_word('inner')
        join = reader.expect_word('join')
        table = IdentifierExpression.consume(reader)
        if reader.curr_value_lower !='on':
            _as = reader.consume_optional_word('as')
            table = AliasedIdentifierExpression(table, _as, reader.expect_any_of([Token.WORD, Token.QUOTED_IDENTIFIER]))
        on = reader.expect_word('on')
        condition = BooleanExpression.consume(reader)
        return JoinExpression(join_type, join, table, on, condition)

class FromExpression(Clause):

    def __init__(self, _from: TokenContext, table: IdentifierExpression, joins: list[JoinExpression]):
        super().__init__([_from, table, *joins])
        self.table = table
        self.joins = joins

    @classmethod
    def consume(cls, reader:Reader):
        from parsing.expressions.scalar_expression import IdentifierExpression, AliasedIdentifierExpression
        _from = reader.expect_word('from')
        if not reader.curr.type in [Token.QUOTED_IDENTIFIER, Token.WORD, Token.VARIABLE]:
            raise ValueError(f"Invalid token: '{reader.curr.value}' ({reader.curr.type})")
        table = IdentifierExpression.consume(reader)
        # todo: gah
        if not reader.eof and reader.curr_value_lower not in ['where', 'order', 'group', 'join', 'inner', 'left', ')']:
            table = AliasedIdentifierExpression(
                table, 
                reader.consume_optional_word('as'),
                reader.expect_any_of([Token.QUOTED_IDENTIFIER, Token.WORD])
            )
        joins: list[JoinExpression] = []
        while reader.curr_value_lower in ['inner', 'left', 'join']:
            joins.append(JoinExpression.consume(reader))
        return FromExpression(_from, table, joins)
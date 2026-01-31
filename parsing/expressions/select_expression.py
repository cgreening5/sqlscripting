from __future__ import annotations
from typing import TYPE_CHECKING
from parsing.expressions.clause import Clause
from parsing.expressions.declare_expression import VariableExpression
from parsing.expressions.scalar_expression import ColumnIdentifierExpression, ParentheticalExpression
from parsing.expressions.token_context import TokenContext
from parsing.expressions.variable_assignment import VariableAssignmentExpression
from parsing.reader import Reader
from parsing.tokenizer import Token

if TYPE_CHECKING:
    from parsing.expressions.scalar_expression import BooleanExpression, IdentifierExpression, TableIdentifierExpression, ScalarExpression, AliasedScalarIdentifierExpression

class SelectExpression(Clause):

    def __init__(
            self, 
            select: TokenContext,
            top: TokenContext,
            top_n: ScalarExpression,
            distinct: TokenContext | None,
            comma_separated_projection: list[ScalarExpression | TokenContext | VariableAssignmentExpression],
            into: IntoExpression,
            _from: FromExpression,
            where: TokenContext,
            predicate: BooleanExpression,
            groupby: GroupByExpression,
            orderby: OrderByExpression,
        ):
        super().__init__([
            select, 
            top, 
            top_n, 
            distinct, 
            *comma_separated_projection, 
            into,
            _from, 
            where, 
            predicate,
        ])
        self.top_n = top_n
        self.distinct = distinct
        self.projection: list[ScalarExpression | AliasedScalarIdentifierExpression | VariableAssignmentExpression] \
            = list(filter(lambda c: not isinstance(c, TokenContext), comma_separated_projection))
        self.into = into
        self._from = _from
        self._predicate = predicate
        self.groupby = groupby
        self.orderby = orderby
        self.produces_resultset = into == None

    @classmethod
    def consume(cls, reader: Reader):
        from parsing.expressions.scalar_expression import ScalarExpression, BooleanExpression, AliasedScalarIdentifierExpression
        select = reader.expect_word('select')
        top = reader.consume_optional_word('top')
        if top:
            top_n = ScalarExpression.consume(reader)
        else:
            top_n = None
        distinct = reader.consume_optional_word('distinct')
        comma_separated_projection = []
        while True:
            if reader.curr_value_lower == '*':
                expression = reader.expect_symbol('*')
            else:
                expression = ScalarExpression.consume(reader)
            if reader.curr_value_lower == 'as':
                expression = AliasedScalarIdentifierExpression(
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
            elif reader.curr_value_lower not in (',', 'from', 'into'):
                expression = AliasedScalarIdentifierExpression(
                    expression,
                    None,
                    reader.expect_any_of([Token.QUOTED_IDENTIFIER, Token.WORD])
                )
            comma_separated_projection.append(expression)
            if reader.curr_value_lower == ',':
                comma_separated_projection.append(reader.expect_symbol(','))
            else:
                break
        into = None
        if reader.curr_value_lower == 'into':
            into = IntoExpression.consume(reader)
        _from = FromExpression.consume(reader)
        where = None
        predicate = None
        if reader.curr_value_lower == 'where':
            where = reader.expect_word('where')
            predicate = BooleanExpression.consume(reader)
        groupby = None
        if reader.curr_value_lower == 'group':
            groupby = GroupByExpression.consume(reader)
        orderby = None
        if reader.curr_value_lower == 'order':
            orderby = OrderByExpression.consume(reader)
        return SelectExpression(
            select,
            top, top_n, 
            distinct, 
            comma_separated_projection, 
            into,
            _from,
            where, 
            predicate,
            groupby,
            orderby
        )

    def trace(self, tracer, column) -> str:
        self.tracer = tracer            
        return column.trace(self)
    
    def resolve_table_identifier(self, table: TableIdentifierExpression):
        table = self._from.resolve_table_identifier(table)
        if self.tracer:
            print(self.tracer.trace_table_identifier(table))
        return table

    def columns(self):
        return self.projection

    def predicate(self):
        return self._predicate
    
class GroupByExpression(Clause):

    def __init__(
        self, 
        group: TokenContext, 
        by: TokenContext, 
        columns: list[ScalarExpression]
    ):
        super().__init__([group, by, *columns])
        self.columns = columns

    @staticmethod
    def consume(reader: Reader):
        from parsing.expressions.scalar_expression import ScalarExpression
        group = reader.expect_word('group')
        by = reader.expect_word('by')
        columns: list[ScalarExpression] = []
        while True:
            columns.append(ScalarExpression.consume(reader))
            if reader.curr_value_lower == ',':
                columns.append(reader.expect_symbol(','))
            else:
                break
        return GroupByExpression(group, by, columns)

class ApplyExpression(Clause):

    def __init__(
        self,
        apply_type,
        apply,
        expression: AliasedScalarIdentifierExpression
    ):
        super().__init__([apply_type, apply, expression])
        self.apply_type = apply_type
        self.expression = expression
  
class JoinExpression(Clause):

    def __init__(
        self, 
        join_type: TokenContext, 
        join: TokenContext, 
        table: TableIdentifierExpression | AliasedScalarIdentifierExpression,
        on: TokenContext, 
        condition: BooleanExpression
    ):
        super().__init__([join_type, join, table, on, condition])
        self.join_type =  join_type
        self.table = table
        self.condition = condition

    @staticmethod
    def consume(reader: Reader):
        from parsing.expressions.scalar_expression import BooleanExpression, TableIdentifierExpression, AliasedScalarIdentifierExpression
        join_type = reader.consume_optional_words('left', 'outer') \
            or reader.consume_optional_word('left') \
            or reader.consume_optional_word('inner') \
            or reader.consume_optional_word('outer') \
            or reader.consume_optional_word('right')
        assert reader.curr_value_lower in ('apply', 'join')
        join = reader.expect_word()
        if reader.curr_value_lower == "(":
            table = ParentheticalExpression.consume(reader)
        else:
            table = TableIdentifierExpression.consume(reader)
        if reader.curr_value_lower !='on':
            _as = reader.consume_optional_word('as')
            table = AliasedTableExpression(table, _as, reader.expect_any_of([Token.WORD, Token.QUOTED_IDENTIFIER]))
        if join.token.value.lower() == 'join':
            on = reader.expect_word('on')
            condition = BooleanExpression.consume(reader)
            return JoinExpression(join_type, join, table, on, condition)
        else:
            return ApplyExpression(join_type, join, table)

class FromExpression(Clause):

    def __init__(self, _from: TokenContext, table: TableIdentifierExpression, joins: list[JoinExpression]):
        super().__init__([_from, table, *joins])
        self.table = table
        self.joins = joins

    @classmethod
    def consume(cls, reader:Reader):
        from parsing.expressions.scalar_expression import TableIdentifierExpression
        _from = reader.expect_word('from')
        if not reader.curr.type in [Token.QUOTED_IDENTIFIER, Token.WORD, Token.VARIABLE, Token.TEMP_TABLE]:
            raise ValueError(f"Invalid token: '{reader.curr.value}' ({reader.curr.type})")
        table = TableIdentifierExpression.consume(reader)
        # todo: gah
        if not reader.eof and reader.curr_value_lower not in ['where', 'order', 'group', 'join', 'inner', 'left', ')', 'select', 'outer']:
            table = AliasedTableExpression(
                table, 
                reader.consume_optional_word('as'),
                reader.expect_any_of([Token.QUOTED_IDENTIFIER, Token.WORD])
            )
        joins: list[JoinExpression] = []
        while reader.curr_value_lower in ['inner', 'left', 'join', 'outer']:
            joins.append(JoinExpression.consume(reader))
        return FromExpression(_from, table, joins)
    
    def resolve_table_identifier(self, table: TableIdentifierExpression) -> TableIdentifierExpression:
        if table is None and self.joins == []:
            return self.table.table
        if isinstance(self.table, AliasedTableExpression) and self.table.alias.token.value.lower() == table.table.token.value.lower():
            return self.table.table
        else:
            for join in self.joins:
                if isinstance(join, JoinExpression):
                    if isinstance(join.table, AliasedTableExpression) and join.table.alias.token.value == table:
                        return join.table.table
        return table

class IntoExpression(Clause):

    def __init__(self, into, dest):
        super().__init__([into, dest])
        self.dest = dest

    @staticmethod
    def consume(reader: Reader) -> Self:
        return IntoExpression(
            reader.expect_word('into'),
            reader.expect(Token.TEMP_TABLE)
        )
    
class AliasedTableExpression(Clause):
    def __init__(
        self, 
        table: TableIdentifierExpression, 
        _as: TokenContext, 
        alias: TokenContext
    ):
        super().__init__([table, _as, alias])
        self.table = table
        self.alias = alias

class OrderByColumnExpression(Clause):
    def __init__(self, column, asc, comma):
        super().__init__([column, asc, comma])
        self.column = column
        self.asc = asc

class OrderByExpression(Clause):
    def __init__(
        self,
        order: TokenContext,
        by: TokenContext,
        columns: OrderByColumnExpression
    ):
        super().__init__([order, by, *columns])
        self.columns = columns

    @staticmethod
    def consume(reader: Reader):
        from parsing.expressions.scalar_expression import ScalarExpression
        order = reader.expect_word('order')
        by = reader.expect_word('by')
        columns = []
        while True:
            column = ScalarExpression.consume(reader),
            asc = reader.consume_optional_word('asc') or reader.consume_optional_word('desc')
            if reader.curr_value_lower == ',':
                columns.append(OrderByColumnExpression(column, asc, reader.expect_symbol(',')))
            else:
                columns.append(OrderByColumnExpression(column, asc, None))
                break
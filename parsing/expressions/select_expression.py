from parsing.expressions.clause import Clause
from parsing.expressions.scalar_expression import BooleanExpression, IdentifierExpression, ScalarExpression
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token

class SelectExpression(Clause):

    def __init__(
            self, 
            select: TokenContext, 
            distinct: TokenContext | None,
            comma_separated_projection: list[ScalarExpression | TokenContext],
            _from: TokenContext
        ):
        super().__init__([select, distinct, *comma_separated_projection, _from])
        self.distinct = distinct
        self.projection = filter(lambda c: isinstance(c, ScalarExpression), comma_separated_projection)

    @classmethod
    def consume(cls, reader: Reader):
        select = reader.expect_word('select')
        distinct = reader.consume_optional_word('distinct')
        comma_separated_projection = []
        while True:
            expression = ScalarExpression.consume(reader)
            if reader.curr_value_lower == 'as':
                expression = AliasedScalarExpression(
                    expression,
                    reader.expect_word('as'),
                    reader.expect_any_of([Token.QUOTED_IDENTIFIER, Token.WORD])
                )
            comma_separated_projection.append(expression)
            if reader.curr_value_lower == ',':
                comma_separated_projection.append(reader.expect_symbol(','))
            else:
                break
        _from = FromExpression.consume(reader)
        return SelectExpression(select, distinct, comma_separated_projection, _from)
    
class AliasedScalarExpression(ScalarExpression):

    def __init__(self, expression, _as, alias):
        super().__init__([expression, _as, alias])
        self.expression = expression
        self.alias = alias
    
class JoinExpression(Clause):

    def __init__(
        self, 
        join_type: TokenContext, 
        join: TokenContext, 
        table: IdentifierExpression | AliasedScalarExpression,
        on: TokenContext, 
        condition: BooleanExpression
    ):
        super().__init__([join_type, join, table, on, condition])
        self.join_type =  join_type
        self.table = table
        self.condition = condition

    def consume(cls, reader: Reader):
        join_type = reader.consume_optional_word('left') \
            or reader.consume_optional_word('inner')
        join = reader.expect_word('join')
        table = IdentifierExpression.consume(reader)
        if reader.curr_value_lower !='on':
            _as = reader.consume_optional_word('as')
            table = AliasedScalarExpression(table, _as, reader.expect_any_of([Token.WORD, Token.QUOTED_IDENTIFIER]))
        _as = reader.consume_optional_word('asl')
        alias = None
        if reader.curr_value_lower != 'on':
            alias = reader.curr_value_lower()
        on = reader.expect_word('on')
        condition = BooleanExpression.consume(reader)
        return JoinExpression(join_type, join, table, _as,  alias, on, condition)

class FromExpression(Clause):

    def __init__(self, _from: TokenContext, table: IdentifierExpression, joins: list[JoinExpression]):
        super().__init__([_from, table, *joins])

    @classmethod
    def consume(cls, reader:Reader):
        _from = reader.expect_word('from')
        assert reader.curr.type in [Token.QUOTED_IDENTIFIER, Token.WORD]
        table = IdentifierExpression.consume(reader)
        # todo: gah
        if reader.curr_value_lower not in ['where', 'order', 'group', 'join', 'inner', 'left']:
            table = AliasedScalarExpression(
                table, 
                reader.consume_optional_word('as'),
                reader.expect_any_of([Token.QUOTED_IDENTIFIER, Token.WORD])
            )
        joins: list[JoinExpression] = []
        while reader.curr_value_lower in ['inner', 'left', 'join']:
            joins.append(JoinExpression)
            return FromExpression(_from, table, joins)
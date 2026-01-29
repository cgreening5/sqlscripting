from parsing.expressions.clause import Clause
from parsing.expressions.scalar_expression import BooleanExpression, ColumnIdentifierExpression, TableIdentifierExpression, ScalarExpression
from parsing.reader import Reader

class ColumnUpdateExpression(Clause):

    def __init__(self, column, equals, val, comma):
        super().__init__([column, equals, val, comma])
        self.column = column
        self.comma = comma

    @staticmethod
    def consume(reader: Reader):
        column = ColumnIdentifierExpression.consume(reader)
        equals = reader.expect_symbol('=')
        val = ScalarExpression.consume(reader)
        comma = reader.expect_symbol(',') if reader.curr_value_lower == ',' else None
        return ColumnUpdateExpression(
            column,
            equals,
            val,
            comma
        )

class UpdateExpression(Clause):

    def __init__(self, update, table, _set, updates, where, predicate):
        super().__init__([update, table, _set, *updates, where, predicate])

    def consume(reader: Reader):
        update = reader.expect_word('update')
        table = TableIdentifierExpression.consume(reader)
        _set = reader.expect_word('set')
        updates = [ColumnUpdateExpression.consume(reader)]
        while updates[-1].comma != None:
            updates.append(ColumnUpdateExpression.consume(reader))
        where = reader.consume_optional_word('where')
        predicate = None
        if where:
            predicate = BooleanExpression.consume(reader)
        return UpdateExpression(
            update,
            table,
            _set,
            updates,
            where,
            predicate
        )
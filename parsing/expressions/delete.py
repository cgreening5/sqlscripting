from parsing.expressions.clause import Clause
from parsing.expressions.scalar_expression import TableIdentifierExpression, ScalarExpression
from parsing.reader import Reader


class DeleteExpression(Clause):

    def __init__(self, delete, _from, table, where, predicate):
        super().__init__([delete, _from, table, where, predicate])
        self.table = table
        self.predicate = predicate

    @staticmethod
    def consume(reader: Reader):
        delete = reader.expect_word('delete')
        _from = reader.consume_optional_word('from')
        table = TableIdentifierExpression.consume(reader)
        if reader.curr_value_lower == 'where':
            return DeleteExpression(
                delete,
                _from,
                table,
                reader.expect_word('where'),
                ScalarExpression.consume(reader),
            )
        return DeleteExpression(
            delete,
            _from,
            table,
            None,
            None
        )
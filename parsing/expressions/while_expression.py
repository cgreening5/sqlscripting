from parsing.expressions.clause import Clause
from parsing.expressions.scalar_expression import BooleanExpression
from parsing.reader import Reader


class WhileExpression(Clause):

    def __init__(self, _while, predicate, block):
        super().__init__([_while, predicate, block])
        self.predicate = predicate
        self.block = block

    @staticmethod
    def consume(reader: Reader):
        from parsing.expressions.block_expression import BeginEndBlock
        return WhileExpression(
            reader.expect_word('while'),
            BooleanExpression.consume(reader),
            BeginEndBlock.consume(reader)
        )
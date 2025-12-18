import unittest

from parsing.expressions.scalar_expression import BooleanOperationExpression
from parsing.reader import Reader
from parsing.tokenizer import Tokenizer

class TestBooleanExpressionParsing(unittest.TestCase):

    def test_equality(self):
        sql = "Column = 'val'"
        reader = Reader(Tokenizer(sql).parse())
        BooleanOperationExpression.consume(reader)
        assert reader.eof

    def test_gte(self):
        sql = "Column >= 'val'"
        reader = Reader(Tokenizer(sql).parse())
        BooleanOperationExpression.consume(reader)
        assert reader.eof
        
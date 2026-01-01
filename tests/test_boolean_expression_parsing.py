import unittest

from parsing.expressions.scalar_expression import BooleanExpression, BooleanOperationExpression, ComparisonExpression, InExpression
from parsing.expressions.select_expression import SelectExpression
from parsing.reader import Reader
from parsing.tokenizer import Tokenizer
from tests.utilities import parse

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
        
    def test_in(self):
        """select Id from Table where Id in (1, 2, 3)"""
        sql = "select Id from Table where Id in (1, 2, 3)"
        clauses = parse(sql)
        select: SelectExpression = clauses[0]
        self.assertIsInstance(select.predicate, InExpression)

    def test_ne(self):
        """select Id from Table where Id != 1"""
        sql = "select Id from Table where Id != 1"
        clauses = parse(sql)
        predicate: ComparisonExpression = clauses[0].predicate
        self.assertEqual(predicate.operation.operator.token.value, '!=')

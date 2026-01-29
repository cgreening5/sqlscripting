from tests.utilities import read
import unittest

from parsing.expressions.scalar_expression import BooleanExpression, BooleanOperationExpression, ComparisonExpression, InExpression, ScalarExpression, ParentheticalScalarExpression
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
        select: SelectExpression = parse(sql).expressions[0]
        self.assertIsInstance(select.predicate(), InExpression)
        
    def test_not_in(self):
        """select Id from Table where Id not in (1, 2, 3)"""
        sql = "select Id from Table where Id not in (1, 2, 3)"
        select: SelectExpression = parse(sql).expressions[0]
        self.assertIsInstance(select.predicate(), InExpression)
        self.assertFalse(select.predicate()._in)

    def test_ne(self):
        """select Id from Table where Id != 1"""
        sql = "select Id from Table where Id != 1"
        block = parse(sql)
        self.assertIsInstance(block.expressions[0].predicate(), BooleanOperationExpression)
        predicate: BooleanOperationExpression = block.expressions[0].predicate
        self.assertEqual(predicate().operator.operator.token.value, '!=')

    def test_parenthesized_not(self):
        """(NOT A = 1) AND B = 2"""
        sql = "(NOT A = 1) AND B = 2"
        boolean = ScalarExpression.consume(read(sql))
        self.assertIsInstance(boolean, BooleanOperationExpression)
        self.assertEqual(boolean.operator.operator.token.value.lower(), 'and')
        # Left side should be a parenthesized NOT expression
        self.assertIsInstance(boolean.left, ParentheticalScalarExpression)
        # Right side should be a comparison expression
        self.assertIsInstance(boolean.right, BooleanOperationExpression)
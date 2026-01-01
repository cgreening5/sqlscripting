import unittest

from parsing.expressions.scalar_expression import BooleanExpression
from parsing.expressions.while_expression import WhileExpression
from parsing.reader import Reader
from parsing.tokenizer import Tokenizer
from tests.utilities import parse


class TestWhile(unittest.TestCase):

    def test_while(self):
        sql = """
            while (var < 1)
                insert into Table (column) values (value)
        """
        #clauses = parse(sql)
        #self.assertIsInstance(clauses[0], WhileExpression)

    def test_something(self):
        sql = """(var < 1)"""
        tokens = Tokenizer(sql).parse()
        BooleanExpression.consume(Reader(tokens))
        
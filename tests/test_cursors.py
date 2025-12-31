import unittest

from parsing.cursor.cursor_expression import CursorExpression
from parsing.parser import Parser
from parsing.tokenizer import Tokenizer


class TestCursors(unittest.TestCase):

    def test_parse_cursor(self):
        sql = "declare testcursor cursor for select Id from table where Id = 1"
        parsed = Parser(Tokenizer(sql).parse()).parse()
        self.assertIsInstance(parsed[0], CursorExpression)
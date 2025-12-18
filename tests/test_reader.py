import unittest

from parsing.reader import Reader
from parsing.tokenizer import Tokenizer


class TestReader(unittest.TestCase):

    def test_expect_from_symbols(self):
        reader = Reader(Tokenizer(">='test'").parse())
        self.assertEqual(reader.expect_from_symbols(['>', '>=']).token.value, '>=')
        self.assertEqual(reader.curr_value_lower, "'test'")
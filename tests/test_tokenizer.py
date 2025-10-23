import unittest
from parsing.tokenizer import Token, Tokenizer

class TestTokenizer(unittest.TestCase):

    def test_tokenize_simple_use(self):
        sql = "USE my_database;"
        self.tokenizer = Tokenizer(sql)
        tokens = self.tokenizer.parse()

        expected_tokens = [
            Token(Token.WORD, 'USE'),
            Token(Token.WHITESPACE, ' '),
            Token(Token.WORD, 'my_database'),
            Token(Token.SYMBOL, ';')
        ]

        self.assertEqual(len(tokens), len(expected_tokens))
        for token, expected in zip(tokens, expected_tokens):
            self.assertEqual(token.type, expected.type)
            self.assertEqual(token.value, expected.value)
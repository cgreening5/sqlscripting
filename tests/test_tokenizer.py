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

        self.assert_tokens_equal(expected_tokens, tokens)

    def test_tokenize_right(self):
        sql = "RIGHT([Column], 4)"
        self.tokenizer = Tokenizer(sql)
        tokens = self.tokenizer.parse()
        self.assert_tokens_equal([
            Token(Token.WORD, 'RIGHT'),
            Token(Token.SYMBOL, '('),
            Token(Token.QUOTED_IDENTIFIER, '[Column]'),
            Token(Token.SYMBOL, ','),
            Token(Token.WHITESPACE, ' '),
            Token(Token.NUMBER, '4'),
            Token(Token.SYMBOL, ')')
        ], tokens)

    def assert_tokens_equal(self, expected, found):
        self.assertEqual(len(expected), len(found), f"Incorrect number of tokens. Expected {expected}, found {found}")

        for expected_token, found_token in zip(expected, found):
            self.assertEqual(expected_token.type, found_token.type)
            self.assertEqual(expected_token.value, found_token.value)
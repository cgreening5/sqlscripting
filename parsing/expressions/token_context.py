from parsing.tokenizer import Token
from typing import Generator


class TokenContext:

    def __init__(self, token: Token, whitespace: Generator[Token]):
        self.token = token
        self.whitespace = list(whitespace)
    
    def __str__(self):
        return f"{self.token}{self.whitespace}"
from parsing.expressions.token_context import TokenContext
from typing import Self

class Clause:

    def __init__(self, tokens: list[TokenContext | Self ]):
        self.tokens = tokens
    
    def __str__(self):
        return ''.join(map(str, filter(lambda t: t is not None, self.tokens)))
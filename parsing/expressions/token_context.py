from parsing.tokenizer import Token
from typing import Generator


class TokenContext:

    def __init__(self, token: Token, whitespace: Generator[Token], type: str=None):
        self.token = token
        self.whitespace = list(whitespace)
        self.type = type or token.type

    def __str__(self):
        return f"{self.token.value}{''.join(str(token) for token in self.whitespace)}"
    
    def uppercase(self):
        if self.type in [Token.VARIABLE, Token.COMMENT, Token.QUOTED_IDENTIFIER, Token.IDENTIFIER]:
            return self.token.value + ''.join(token.value for token in self.whitespace)
        else:
            return self.token.value.upper() + ''.join(token.value for token in self.whitespace)
        
    def lowercase(self):
        if self.type in [Token.VARIABLE, Token.COMMENT, Token.QUOTED_IDENTIFIER, Token.IDENTIFIER]:
            return self.token.value + ''.join(token.value for token in self.whitespace)
        else:
            return self.token.value.lower() + ''.join(token.value for token in self.whitespace)
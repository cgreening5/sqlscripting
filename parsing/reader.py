from typing import Generator, Self
import typing
from parsing.expressions.token_context import TokenContext
from parsing.tokenizer import Token


class Reader:

    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._position = 0
        self.state_stack = []

    @property
    def curr(self) -> Token:
        return self._tokens[self._position]
    
    @property
    def curr_value_lower(self) -> str:
        if self.eof:
            return None
        return self.curr.value.lower()

    def reset(self):
        self._position = 0

    @property
    def eof(self) -> bool:
        return self._position >= len(self._tokens)

    def read(self) -> Token:
        curr = self.curr
        self._position += 1
        return curr

    def print(self, end: int=None, start=0) -> str:
        if end == None:
            end = self._position
        return ''.join(map(str, self._tokens[start: end]))

    def consume_whitespace(self) -> Generator[Token]:
        while not self.eof and self.curr.type in (Token.WHITESPACE, Token.NEWLINE, Token.COMMENT):
            yield self.read()

    def expect(self, type: str, value:str=None) -> TokenContext:
        token = self.read()
        if token.type != type:
            if value is not None and token.value.upper() != value.upper():
                raise Exception(f"Expected token of type {type} with value {value}, got {token.__repr__()} at position {self._position}")
            else:
                raise Exception(f"Expected token of type {type}, got {token.__repr__()} at position {self._position}")
        elif value is not None and token.value.upper() != value.upper():
            raise Exception(f"Expected token of type {type} with value {value}, got {token.__repr__()} at position {self._position}")
        return TokenContext(token, self.consume_whitespace())

    def expect_word(self, value:str=None) -> TokenContext:
        return self.expect(Token.WORD, value)
    
    def expect_keyword(self, value:str=None) -> TokenContext:
        word = self.expect_word(value)
        word.token.type = Token.KEYWORD
        return word
    
    def expect_identifier(self, value:str=None) -> TokenContext:
        identifier = self.expect_any_of([Token.WORD, Token.QUOTED_IDENTIFIER])
        if identifier.token.type == Token.WORD:
            identifier.token.type = Token.IDENTIFIER
        return identifier
    
    def expect_any_of(self, types: list[str]) -> TokenContext:
        assert self.curr.type in types, f'invalid token: {self.curr.value} ({self.curr.type})' \
            + f' expected any of {types}'
        return self.expect(self.curr.type)
    
    def consume_optional_words(self, *values:str) -> TokenContext:
        tokens = []
        for value in values:
            if self.curr_value_lower == value:
                tokens.append(self.expect_word(value))
            else: return None
        return tokens

    def consume_optional_word(self, value:str) -> TokenContext:
        if self.curr_value_lower == value:
            return self.expect_word(value)

    def expect_symbol(self, value: str) -> TokenContext:
        return self.expect(Token.SYMBOL, value)
    
    def expect_args(self, *consumers, repeat_consumer=None):
        expressions_or_tokens = []
        parameters = []
        expressions_or_tokens.append(self.expect_symbol('('))
        parameter = consumers[0](self)
        expressions_or_tokens.append(parameter)
        parameters.append(parameter)
        for consumer in consumers[1:]:
            expressions_or_tokens.append(self.expect_symbol(','))
            parameter = consumer(self)
            expressions_or_tokens.append(parameter)
            parameters.append(parameter)
        if repeat_consumer != None:
            while self.curr_value_lower != ')':
                expressions_or_tokens.append(self.expect_symbol(','))
                parameter = repeat_consumer(self)
        expressions_or_tokens.append(self.expect_symbol(')'))
        return expressions_or_tokens, parameters
    
    def _pattern(self, i):
        tokens = self._tokens[self._position : min(self._position + i, len(self._tokens))]
        return ''.join([token.value for token in tokens])

    def peek(self, i=1):
        if self._position + i + 1 >= len(self._tokens):
            return []
        return [token.value.lower() for token in self._tokens[self._position + 1, self._position + 1 + i]]

    def consume_symbol_from(self, patterns: list[str]):
        matches = [pattern for pattern in patterns if pattern == self._pattern(len(pattern))]
        if len(matches) == 0:
            return None
        match = max(matches, key=lambda match: len(match))
        read = ''
        while len(read) < len(match):
            read += self.read().value
        return TokenContext(Token(Token.SYMBOL, read), self.consume_whitespace())
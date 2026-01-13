from parsing.expressions.block_expression import BlockExpression
from parsing.reader import Reader
from parsing.tokenizer import Token

class Parser():

    def __init__(self, tokens: list[Token]):
        self.reader = Reader(tokens)

    def throw(self, err: str | Exception):
        if isinstance(err, str):
            raise ValueError(f"{self.reader.print()}\n{err}")
        else:
            raise ValueError(f"{self.reader.print()}\n{err}") from err
        
    def parse(self) -> BlockExpression:
        try:
            return BlockExpression.consume(self.reader)
        except Exception as e:
            self.throw(e)
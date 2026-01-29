from parsing.expressions.block_expression import BlockExpression
from parsing.expressions.clause import Clause
from parsing.parser import Parser
from parsing.reader import Reader
from parsing.tokenizer import Tokenizer


def parse(sql: str) -> BlockExpression:
    return Parser(Tokenizer(sql).parse()).parse()

def read(sql: str) -> Reader:
    return Reader(Tokenizer(sql).parse())
from parsing.expressions.block_expression import BlockExpression
from parsing.expressions.clause import Clause
from parsing.parser import Parser
from parsing.tokenizer import Tokenizer


def parse(sql: str) -> BlockExpression:
    return Parser(Tokenizer(sql).parse()).parse()
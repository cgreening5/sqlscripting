from parsing.expressions.clause import Clause
from parsing.parser import Parser
from parsing.tokenizer import Tokenizer


def parse(sql: str) -> list[Clause]:
    return Parser(Tokenizer(sql).parse()).parse()
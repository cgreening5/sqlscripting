from parsing.expressions.clause import Clause
from parsing.reader import Reader
from parsing.tokenizer import Token


class BeginTransactionExpression(Clause):

    def __init__(self, begin, tran, tranname):
        super().__init__([begin, tran, tranname])

    @staticmethod
    def consume(reader: Reader):
        begin = reader.expect_word('begin')
        assert reader.curr_value_lower in ('tran', 'transaction')
        tran = reader.expect_word()
        if not reader.eof and reader.curr.type == Token.VARIABLE:
            tranname = reader.expect(Token.VARIABLE)
        else:
            tranname = None
        return BeginTransactionExpression(
            begin,
            tran, 
            tranname
        )
    
class CommitTransactionExpression(Clause):

    def __init__(self, commit, transaction, tranname):
        super().__init__([commit, transaction, tranname])
        self.tranname = tranname

    @staticmethod
    def consume(reader: Reader):
        commit = reader.expect_word('commit')
        assert reader.curr_value_lower in ['tran', 'transaction']
        tran = reader.expect_word()
        if not reader.eof and reader.curr.type == Token.VARIABLE:
            tranname = reader.expect(Token.VARIABLE)
        else: tranname = None
        return CommitTransactionExpression(   
            commit,
            tran,
            tranname
        )
from parsing.expressions.clause import Clause
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token

class TextDataTypeClause(Clause):
    TEXT_TYPES = ('CHAR', 'NCHAR', 'VARCHAR', 'NVARCHAR', 'TEXT', 'NTEXT')
    def __init__(self, datatype: TokenContext, open_paren: TokenContext, length: TokenContext, close_paren: TokenContext):
        assert datatype.token.value.upper() in self.TEXT_TYPES
        super().__init__([datatype, open_paren, length, close_paren])
        self.datatype = datatype
        self.length = length

class DataTypeClause(Clause):
    def __init__(self, datatype: TokenContext):
        super().__init__([datatype])
        self.datatype = datatype

    @staticmethod
    def consume(reader: Reader):

        datatype = reader.expect_word()
        if datatype.token.value.upper() in TextDataTypeClause.TEXT_TYPES:
            open_paren = reader.expect_symbol('(')
            length = reader.expect(Token.NUMBER)
            close_paren = reader.expect_symbol(')')
            return TextDataTypeClause(datatype, open_paren, length, close_paren)
        else:   
            return DataTypeClause(datatype)
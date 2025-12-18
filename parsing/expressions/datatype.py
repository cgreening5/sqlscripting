from parsing.expressions.clause import Clause
from parsing.expressions.token_context import TokenContext

class DataTypeClause(Clause):
    def __init__(self, datatype: TokenContext):
        super().__init__(self, [datatype])
        self.datatype = datatype

    def __repr__(self):
        return f"DataTypeClause(datatype='{self.datatype}')"
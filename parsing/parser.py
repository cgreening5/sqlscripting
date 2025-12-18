from parsing.expressions.block_expression import BlockExpression
from parsing.expressions.clause import Clause
from parsing.expressions.scalar_expression import CastExpression, ConcatExpression, RightExpression, ScalarExpression
from parsing.expressions.select_expression import SelectExpression
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token
    
class VariableReferenceClause(Clause):
    def __init__(self, type, at, varname):
        super().__init__('@', [at, varname])

class DefineTableClause(Clause):
    def __init__(self, open_paren: TokenContext, columns: list[tuple[TokenContext, Clause]], close_paren: TokenContext):
        tokens: list[TokenContext] = [open_paren]
        for column in columns:
            tokens.extend(column)
        tokens.append(close_paren)
        super().__init__(tokens)
        self.open_paren = open_paren
        self.columns = columns
        self.close_paren = close_paren

    def __repr__(self):
        return f"DefineTableClause(columns={self.columns})"
        
class ValuesListClause(Clause):
    def __init__(self, values: TokenContext, openparenthesis: TokenContext, comma_seperated_values: list[TokenContext], closeparenthesis):
        super().__init__([values, openparenthesis] + comma_seperated_values + [closeparenthesis])
        self.values = filter(lambda v: v.value != ',',  comma_seperated_values)

class InsertValuesClause(Clause):
    def __init__(
            self, 
            insert: TokenContext, 
            into: TokenContext, 
            table: TokenContext | VariableReferenceClause, 
            colnames: list[TokenContext],
            values_lists: list[ValuesListClause]
        ):
        super().__init__(self, [insert, into, table, *colnames, *values_lists])
        self.table = table
        self.colnames = colnames
        self.values_lists = values_lists

class InsertSelectClause(Clause):
    def __init__(
        self,
        insert: TokenContext,
        into: TokenContext,
        table: TokenContext,
        select_clause: Clause,
    ):
        super().__init__(self, [insert, into, table, select_clause])
        self.table = table
        self.select_clause = select_clause

class Parser():

    def __init__(self, tokens: list[Token]):
        self.reader = Reader(tokens)

    def throw(self, err: str | Exception):
        if isinstance(err, str):
            raise ValueError(f"{self.reader.print()}\n{err}")
        else:
            raise ValueError(f"{self.reader.print()}\n{err}") from err
        
    def parse(self) -> list[Clause]:
        try:
            return BlockExpression.consume(self.reader)
        except Exception as e:
            self.throw(e)

    @property
    def _curr(self):
        return self.reader.curr
    
    def _read(self):
        return self.reader.read()
        
    def _consume_table_definition(self):
        columns = []
        open_paren = TokenContext(
            self._expect(Token.SYMBOL, '('),
            list(self._consume_whitespace_and_newlines())
        )
        variable = TokenContext(
            self._expect(Token.WORD),
            list(self._consume_whitespace_and_newlines())
        )
        datatype = self.expect_datatype()
        columns.append([variable, datatype])
        while self._curr.type == Token.SYMBOL and self._curr.value == ',':
            comma = TokenContext(
                self._expect(Token.SYMBOL, ','),
                self._consume_whitespace_and_newlines()
            )
            columns[-1].append(comma)
            variable = TokenContext(
                self._expect(Token.WORD),
                self._consume_whitespace_and_newlines()
            )
            print(variable)
            datatype = self.expect_datatype()
            columns.append((variable, datatype))
        close_paren = TokenContext(
            self._expect(Token.SYMBOL, ')'),
            self._consume_end_of_statement()
        )
        return DefineTableClause(open_paren, columns, close_paren)

    def _consume_insert_values(self, insert: TokenContext, into: TokenContext, table: TokenContext):
        open_parentheses = self._expect_tokencontext(Token.SYMBOL, '(')
        colnames = []
        while True:
            colnames.append(self._expect_tokencontext(Token.WORD))
            if self._curr.value != ')':
                colnames.append(self._expect_tokencontext(Token.SYMBOL, ','))
            else:
                if self._curr.value.lower() == 'values':
                    values = self._expect_tokencontext(Token.WORD, 'values')
                    values_list = self._consumes_values_list()
                    return InsertValuesClause(
                        insert,
                        into,
                        table,
                        colnames,
                        values,
                        [values_list]
                    )

    def _consume_insert_select(self):
        pass

    def _consumes_values_list(self) -> ValuesListClause:
        values = self._expect_tokencontext(values),
        open_parenthesis = self._expect_tokencontext(Token.SYMBOL, '(')
        col_values = []
        while True:
            col_values.append(self._expect_tokencontext(Token.NUMBER))
            if self._curr.value == ',':
                col_values.append(self._expect_tokencontext(Token.SYMBOL, ','))
            else:
                close_parenthesis = self._expect_tokencontext(Token.SYMBOL, '(')
                return ValuesListClause(
                    values,
                    open_parenthesis,
                    col_values,
                    close_parenthesis
                )            

    # Utilities
    def _consume_whitespace_and_newlines(self):
        while self._curr.type in (Token.WHITESPACE, Token.NEWLINE):
            yield self._read()

    def _consume_expected_whitespace_and_newlines(self):
        assert self._curr.type in (Token.WHITESPACE, Token.NEWLINE)
        return self._consume_whitespace_and_newlines()

    def _consume_end_of_statement(self):
        while self._curr is not None and self._curr.type == Token.WHITESPACE:
            yield self._read()
        if self._curr is not None and ((self._curr.type == Token.SYMBOL and self._curr.value == ';') or self._curr.type == Token.NEWLINE):
            yield self._read()
        elif self._curr is not None:
            self.throw(f"Expected end of statement, found '{self._curr}'")

    def _expect(self, type: str, value: str = None):
        token = self._read()
        if token.type != type:
            if value is not None and token.value.upper() != value.upper():
                self.throw(f"Expected token of type {type} with value {value}, got {token.__repr__()} at position {self.reader._position}")
            else:
                self.throw(f"Expected token of type {type}, got {token.__repr__()} at position {self.reader._position}")
        elif value is not None and token.value.upper() != value.upper():
            self.throw(f"Expected token of type {type} with value {value}, got {token.__repr__()} at position {self.reader._position}")
        return token

    def _expect_tokencontext(self, type: str, value: str=None, expect_newlines=False):
        token = self._expect(type, value)
        if expect_newlines:
            whitespace = self._consume_expected_whitespace_and_newlines()
        else:
            whitespace = self._consume_whitespace_and_newlines()
        return TokenContext(token, whitespace)

    def _expect_word(self, value: str=None, expect_whitespace=False):
        return self._expect_tokencontext(Token.WORD, value, expect_whitespace)

    def _expect_symbol(self, value: str, expect_whitespace=False):
        return self._expect_tokencontext(Token.SYMBOL, value, expect_whitespace)
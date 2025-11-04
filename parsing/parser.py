from parsing.tokenizer import Token
class TokenContext:

    def __init__(self, token: Token, whitespace: list[Token]):
        self.token = token
        self.whitespace = whitespace

class Clause:

    def __init__(self, type: str, tokens: list[TokenContext]):
        self.type = type
        self.tokens: list[Token|Clause] = tokens
    
    def __str__(self):
        return ''.join(map(str, self.tokens))

class UseClause(Clause):
    def __init__(self, use: TokenContext, database: TokenContext):
        super().__init__('USE', [use, database])
        self.use = use
        self.database = database

    def __repr__(self):
        return f"UseClause(database='{self.database}')"
    
class DeclareVariableClause(Clause):
    def __init__(self, declare: TokenContext, variable: TokenContext, as_token: TokenContext, datatype: Clause, end_of_statement: list[Token]):
        super().__init__('DECLARE', [declare, variable, as_token, datatype] + end_of_statement)
        self.declare = declare
        self.variable = variable
        self.datatype = datatype


    def __repr__(self):
        return f"DeclareClause(variable='{self.variable}', datatype='{self.datatype}')"

class DefineTableClause(Clause):
    def __init__(self, open_paren: TokenContext, columns: list[tuple[TokenContext, Clause]], close_paren: TokenContext):
        tokens: list[TokenContext] = [open_paren]
        for column in columns:
            tokens.extend(column)
        tokens.append(close_paren)
        super().__init__('TABLE_DECLARATION', tokens)
        self.open_paren = open_paren
        self.columns = columns
        self.close_paren = close_paren

    def __repr__(self):
        return f"DefineTableClause(columns={self.columns})"
    
class DataTypeClause(Clause):
    def __init__(self, datatype: TokenContext):
        super().__init__('DATATYPE', [datatype])
        self.datatype = datatype

    def __repr__(self):
        return f"DataTypeClause(datatype='{self.datatype}')"
    
class TextDataTypeClause(Clause):
    TEXT_TYPES = ('CHAR', 'NCHAR', 'VARCHAR', 'NVARCHAR', 'TEXT', 'NTEXT')
    def __init__(self, datatype: TokenContext, open_paren: TokenContext, length: TokenContext, close_paren: TokenContext):
        assert datatype.token.value.upper() in self.TEXT_TYPES
        super().__init__('TEXT_DATATYPE', [datatype, open_paren, length, close_paren])
        self.datatype = datatype
        self.length = length

    def __repr__(self):
        return f"TextDataTypeClause(datatype='{self.datatype}', length='{self.length}')"
    
class DeclareTableVariableClause(Clause):
    def __init__(self, declare: TokenContext, name: TokenContext, as_token: TokenContext, table: TokenContext, table_definition: DefineTableClause):
        super().__init__('DECLARE_TABLE', [declare, name, as_token, table] + table_definition.tokens)
        self.declare = declare
        self.name = name
        self.table_definition = table_definition

    def __repr__(self):
        return f"DeclareTableVariableClause(variable='{self.variable}', table_definition={self.table_definition})"

class Parser():

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.position = 0

    def parse(self) -> list[Clause]:
        self.position = 0
        clauses: list[Clause] = []
        while self.position < len(self.tokens):
            token = self._curr()
            if token.type in (token.WHITESPACE, token.NEWLINE):
                self._read()
                continue
            elif token.type == token.WORD:
                if token.value.upper() == 'USE':
                    clauses.append(self._consume_use())
                elif token.value.upper() == 'DECLARE':
                    clauses.append(self._consume_declare())
                else:
                    raise ValueError(f"Unexpected token '{token.__repr__()}'")
            else:
                raise ValueError(f"Unexpected token '{token.__repr__()}'")
        return clauses

    def _curr(self):
        return self.tokens[self.position]
    
    def _read(self):
        token = self._curr()
        self.position += 1
        return token   

    def _consume_use(self):
        use = self._expect(Token.WORD, 'USE')
        whitespace = list(self._consume_expected_whitespace_and_newlines())
        database = self._expect(Token.WORD)
        end_of_statement = list(self._consume_end_of_statement())
        return UseClause(TokenContext(use, whitespace), TokenContext(database, end_of_statement))
    
    def _consume_declare(self):
        declare = TokenContext(
            self._expect(Token.WORD, 'DECLARE'),
            list(self._consume_expected_whitespace_and_newlines())
        )
        variable = TokenContext(
            self._expect(Token.VARIABLE),
            list(self._consume_expected_whitespace_and_newlines())
        )

        if self._curr().type == Token.WORD and self._curr().value.upper() == 'AS':
            as_token = TokenContext(
                self._expect(Token.WORD, 'AS'),
                list(self._consume_expected_whitespace_and_newlines())
            )
        else:
            as_token = None
        if self._curr().type == Token.WORD and self._curr().value.upper() == 'TABLE':
            table = TokenContext(self._expect(Token.WORD, 'TABLE'), list(self._consume_expected_whitespace_and_newlines()))
            table_expression = self._consume_table_definition()
            return DeclareTableVariableClause(declare, variable, table, as_token, table_expression)
        else:
            datatype = self.expect_datatype()
            end_of_statement = list(self._consume_end_of_statement())
            return DeclareVariableClause(declare, variable, as_token, datatype, end_of_statement)
        
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
        while self._curr().type == Token.SYMBOL and self._curr().value == ',':
            comma = TokenContext(
                self._expect(Token.SYMBOL, ','),
                list(self._consume_whitespace_and_newlines())
            )
            columns[-1].append(comma)
            variable = TokenContext(
                self._expect(Token.WORD),
                self._consume_whitespace_and_newlines()
            )
            datatype = self.expect_datatype()
            columns.append((variable, datatype))
        close_paren = TokenContext(
            self._expect(Token.SYMBOL, ')'),
            list(self._consume_end_of_statement())
        )
        return DefineTableClause(open_paren, columns, close_paren)
        
    def expect_datatype(self) -> TokenContext:
        datatype = TokenContext(
            self._expect(Token.WORD),
            list(self._consume_whitespace_and_newlines())
        )
        if datatype.token.value in TextDataTypeClause.TEXT_TYPES:
            open_paren = TokenContext(
                self._expect(Token.SYMBOL, '('),
                list(self._consume_whitespace_and_newlines())
            )
            length = TokenContext(
                self._expect(Token.NUMBER),
                list(self._consume_whitespace_and_newlines())
            )
            close_paren = TokenContext(
                self._expect(Token.SYMBOL, ')'),
                list(self._consume_whitespace_and_newlines())
            )
            return TextDataTypeClause(datatype, open_paren, length, close_paren)
        else:   
            return DataTypeClause(datatype)

    # Utilities
    def _consume_whitespace_and_newlines(self):
        while self._curr().type in (Token.WHITESPACE, Token.NEWLINE):
            yield self._read()

    def _consume_expected_whitespace_and_newlines(self):
        assert self._curr().type in (Token.WHITESPACE, Token.NEWLINE)
        return self._consume_whitespace_and_newlines()

    def _consume_end_of_statement(self):
        while self._curr is not None and self._curr().type == Token.WHITESPACE:
            yield self._read()
        if self._curr is not None and ((self._curr().type == Token.SYMBOL and self._curr().value == ';') or self._curr().type == Token.NEWLINE):
            yield self._read()
        elif self._curr is not None:
            raise ValueError(f"Expected end of statement, found '{self._curr()}' @ {''.join(map(str, self.tokens[:self.position]))}")

    def _expect(self, type: str, value: str = None):
        token = self._read()
        if token.type != type:
            if value is not None and token.value.upper() != value.upper():
                raise ValueError(f"Expected token of type {type} with value {value}, got {token.__repr__()} at {''.join(map(str, self.tokens[:self.position]))}")
            else:
                raise ValueError(f"Expected token of type {type}, got {token.__repr__()} at {''.join(map(str, self.tokens[:self.position]))}")
        elif value is not None and token.value.upper() != value.upper():
            raise ValueError(f"Expected token of type {type} with value {value}, got {token.__repr__()} at {''.join(map(str, self.tokens[:self.position]))}")
        return token
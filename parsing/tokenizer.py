class Token:

    QUOTED_IDENTIFIER = 'QUOTED_IDENTIFIER'
    WORD = 'WORD'
    KEYWORD = 'KEYWORD'
    IDENTIFIER = 'IDENTIFIER'
    WHITESPACE = 'WHITESPACE'
    NEWLINE = 'NEWLINE'
    COMMENT = 'COMMENT'
    VARIABLE = 'VARIABLE'
    SYMBOL = 'SYMBOL'
    NUMBER = 'NUMBER'

    def __init__(self, type: str, value: str):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, '{self.value.replace('\n', '\\n').replace('\r', '\\r')}')"
    
    def __str__(self):
        return self.value
    
    def uppercase(self):
        return self.value.upper()

class Tokenizer:

    def __init__(self, sql: str):
        self.sql = sql
        self._position = 0
        self.length = len(sql)

    @property
    def _curr(self) -> str:
        if self._position < self.length:
            return self.sql[self._position]
        return None

    def parse(self) -> list[Token]:
        tokens = []
        while self._curr is not None:
            char = self._curr
            if char == '-':
                tokens.append(self._consume_comment_or_dash())
            elif char in '+-*/=(),;':
                tokens.append(Token(Token.SYMBOL, char))
                self._position += 1
                continue
            elif char in '\n\r':
                tokens.append(self._consume_newline())
            elif char.isspace():
                tokens.append(self._consume_whitespace())
            elif char.isalpha() or char == '_':
                tokens.append(self._consume_word())
            elif char in '\'"`':
                tokens.append(self._consume_quoted_identifier(char))
            elif char == '[':
                tokens.append(self._consume_quoted_identifier(']'))
            elif char.isdigit():
                tokens.append(self._consume_number())
            elif char == '@':
                tokens.append(self._consume_variable())
            elif char in '.><=+-!':
                tokens.append(self._consume_symbol())
            elif char == ']':
                print('\n'.join(map(repr, tokens)))
                raise ValueError(f"Unmatched closing bracket at {self._get_line_and_column()}")
            else:
                line, col = self._get_line_and_column()
                raise ValueError(f"Unexpected character '{char}' at line {line + 1}, column {col + 1}")
        return tokens

    def _consume_whitespace(self) -> Token:
        if not self._curr.isspace() or self._curr in '\n\r':
            raise Exception("Cannot call on non-whitespace")
        start = self._position
        while self._curr is not None and self._curr.isspace():
            self._position += 1
        return Token(Token.WHITESPACE, self.sql[start:self._position])

    def _consume_word(self) -> Token:
        assert self._curr is not None and (self._curr == '_' or self._curr.isalnum()), \
            f"Error at {self._get_line_and_column()}: Expected alphanumeric or '_, found {self._curr}"
        start = self._position
        while self._curr is not None and (self._curr.isalnum() or self._curr == '_'):
            self._position += 1
        return Token(Token.WORD, self.sql[start:self._position])

    def _consume_quoted_identifier(self, quote_char: str) -> Token:
        start = self._position
        self._position += 1
        while self._curr is not None and self._curr != quote_char:
            self._position += 1
        if self._curr == quote_char:
            self._position += 1
            return Token(Token.QUOTED_IDENTIFIER, self.sql[start:self._position])
        self._raise_error("Unterminated quoted identifier")

    def _consume_comment_or_dash(self) -> Token:
        start = self._position
        self._position += 1
        if self._curr == '-':
            self._position += 1
            while self._curr is not None and self._curr not in '\n\r':
                self._position += 1
            return Token(Token.COMMENT, self.sql[start:self._position])
        return Token(Token.SYMBOL, '-')
    
    def _consume_number(self) -> Token:
        start = self._position
        while self._curr is not None and self._curr.isdigit():
            self._position += 1
        if self._curr == '.':
            self._position += 1
            while self._curr is not None and self._curr.isdigit():
                self._position += 1
        return Token(Token.NUMBER, self.sql[start:self._position])
    
    def _consume_variable(self) -> Token:
        ch = self._read()
        assert ch == '@'
        if self._curr == '@':
            ch += self._read()
        token = self._consume_word()
        token.type = Token.VARIABLE
        token.value = ch + token.value
        return token
    
    def _consume_newline(self) -> Token:
        assert self._curr in '\n\r'
        if self._read() == '\n':
            if self._curr == '\r':
                self._read()
                return Token(Token.NEWLINE, '\n\r')
            return Token(Token.NEWLINE, '\n')
        else:
            return Token(Token.NEWLINE, '\r')
    
    def _get_line_and_column(self) -> Token:
        pos = 0
        line = 0
        col = 0
        while pos < self._position:
            col += 1
            if self.sql[pos] == '\n':
                line += 1
                col = 0
                pos += 1
                if self.sql[pos] == '\r':
                    pos += 1
            else:
                if self.sql[pos] == '\r':
                    line += 1
                    col = 0
                pos += 1
        return line, col
    
    def _read(self):
        ch = self._curr
        self._position += 1
        return ch

    def _consume_symbol(self) -> Token:
        return Token(Token.SYMBOL, self._read())
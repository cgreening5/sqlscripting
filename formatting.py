from parsing.tokenizer import Tokenizer, Token

KEYWORDS = [
    'WHEN',
    'MAX',
    'PROGRAMS',
    'LEN',
    'GROUP',
    'BY',
    'DATE',
    'SUBSTRING',
    'GETDATE',
    '1',
    'DISTINCT',
    'NAME',
    'REPLACE',
    'NVARCHAR',
    'ON',
    'USE',
    'THEN',
    'WHERE',
    'RIGHT',
    'OR',
    'AS',
    'DECLARE',
    'FROM',
    'CONCAT',
    'JOIN',
    'AND',
    'FORMAT',
    'INSERT',
    'TABLE',
    'INTO',
    'SELECT',
    'END',
    'CAST',
    'CASE',
    'IN',
]

class UpperCaseFormatter:
    def format(self, sql: str) -> str:
        tokens = Tokenizer(sql).parse()
        formatted_sql = []
        for token in tokens:
            if token.type in (Token.WORD) and token.value.upper() in KEYWORDS:
                formatted_sql.append(token.value.upper())
            else:
                formatted_sql.append(token.value)
        return ''.join(formatted_sql)
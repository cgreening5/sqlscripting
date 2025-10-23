
from parsing.tokenizer import Token, Tokenizer
import unittest
from parsing.parser import DataTypeClause, DeclareTableVariableClause, DeclareVariableClause, Parser, UseClause


class TestParser(unittest.TestCase):

    def tokenize(self, sql: str) -> list[Token]:
        tokenizer = Tokenizer(sql)
        return tokenizer.parse()

    def test_use_clause(self):
        
        self.parser = Parser(self.tokenize("USE my_database;"))
        parsed_clauses = self.parser.parse()

        self.assertEqual(len(parsed_clauses), 1)
        use_clause = parsed_clauses[0]
        self.assertIsInstance(use_clause, UseClause)
        self.assertEqual(use_clause.database.token.value, 'my_database')

    def test_declare_clause(self):
        """DECLARE @var INT;"""
        self.parser = Parser(self.tokenize("DECLARE @var INT;"))
        parsed_clauses = self.parser.parse()

        self.assertEqual(len(parsed_clauses), 1)
        declare_clause = parsed_clauses[0]
        self.assertIsInstance(declare_clause, DeclareVariableClause)
        self.assertEqual(declare_clause.variable.token.value, '@var')
        self.assertEqual(declare_clause.datatype.datatype.token.value, 'INT')

    def test_declare_clause_with_as(self):
        """DECLARE @var AS INT;"""
        self.parser = Parser(self.tokenize("DECLARE @var AS INT;"))
        parsed_clauses = self.parser.parse()
        self.assertEqual(len(parsed_clauses), 1)
        declare_clause = parsed_clauses[0]  
        self.assertIsInstance(declare_clause, DeclareVariableClause)
        self.assertEqual(declare_clause.variable.token.value, '@var')
        self.assertIsInstance(declare_clause.datatype, DataTypeClause)
        self.assertEqual(declare_clause.datatype.datatype.token.value, 'INT')

    def test_declare_table_clause(self):
        """DECLARE @var AS TABLE (id INT);"""
        self.parser = Parser(self.tokenize("DECLARE @var AS TABLE (id INT);"))
        parsed_clauses = self.parser.parse()

        self.assertEqual(len(parsed_clauses), 1)
        declare_clause = parsed_clauses[0]
        self.assertIsInstance(declare_clause, DeclareTableVariableClause)
        self.assertEqual(declare_clause.name.token.value, '@var')
        table_def = declare_clause.table_definition
        self.assertEqual(len(table_def.columns), 1)
        column_name, column_type = table_def.columns[0]
        self.assertEqual(column_name.token.value, 'id')
        self.assertEqual(column_type.datatype.token.value, 'INT')
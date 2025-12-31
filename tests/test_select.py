import unittest
from parsing.expressions.scalar_expression import AliasedScalarExpression, IdentifierExpression
from parsing.expressions.select_expression import SelectExpression
from tests.utilities import parse

class TestSelect(unittest.TestCase):

    def test_select(self):
        """select Id from Table"""
        clauses = parse("""select Id from Table""")
        self.assertIsInstance(clauses[0], SelectExpression)
        self.assertEqual(1, len(clauses[0].projection))

    def test_select_with_alias(self):
        """select Id from Table t"""
        clauses = parse("""select Id from Table t""")
        select: SelectExpression = clauses[0]
        self.assertIsInstance(select._from.table, AliasedScalarExpression)

    def test_select_with_as_alias(self):
        """select Id from Table as t"""
        clauses = parse("""select Id from Table t""")
        select: SelectExpression = clauses[0]
        self.assertIsInstance(select._from.table, AliasedScalarExpression)

    def test_select_with_aliased_join(self):
        """select Id from Table T1 join Table t2"""
        clauses = parse("""select Id from Table T1 join Table t2 on T1.Id = T2.Id""")
        select: SelectExpression = clauses[0]
        self.assertIsInstance(select._from.joins[0].alias, AliasedScalarExpression)

    def test_select_with_join(self):
        """select Id from Table T1 join Table t2"""
        clauses = parse("""select Id from Table1 join Table2 on Table1.Id = Table2.Id""")
        select: SelectExpression = clauses[0]
        self.assertIsInstance(select._from.joins[0].table, IdentifierExpression)
        self.assertIsNone(select._from.joins[0].alias)
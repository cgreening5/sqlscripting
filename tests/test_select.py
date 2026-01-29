import unittest
from parsing.expressions.scalar_expression import AliasedScalarIdentifierExpression, IdentifierExpression, TableIdentifierExpression
from parsing.expressions.select_expression import AliasedTableExpression, SelectExpression
from tests.utilities import parse

class TestSelect(unittest.TestCase):

    def test_select(self):
        """select Id from Table"""
        block = parse("""select Id from Table""")
        self.assertIsInstance(block.expressions[0], SelectExpression)
        self.assertEqual(1, len(block.expressions[0].projection))

    def test_select_with_alias(self):
        """select Id from Table t"""
        block = parse("""select Id from Table t""")
        select: SelectExpression = block.expressions[0]
        self.assertIsInstance(select._from.table, AliasedTableExpression)

    def test_select_with_as_alias(self):
        """select Id from Table as t"""
        block = parse("""select Id from Table t""")
        select: SelectExpression = block.expressions[0]
        self.assertIsInstance(select._from.table, AliasedTableExpression)

    def test_select_with_aliased_join(self):
        """select Id from Table T1 join Table t2"""
        block = parse("""select Id from Table T1 join Table t2 on T1.Id = T2.Id""")
        select: SelectExpression = block.expressions[0]
        self.assertIsInstance(select._from.joins[0].table, AliasedTableExpression)

    def test_select_with_join(self):
        """select Id from Table T1 join Table t2"""
        select: SelectExpression = parse(
            """select Id from Table1 join Table2 on Table1.Id = Table2.Id"""
        ).expressions[0]
        self.assertIsInstance(select._from.joins[0].table, TableIdentifierExpression)

    def test_multiple_selects(self):
        """select ID fromtable1\nselect Name from table2"""
        block = parse(
            """select ID from table1\nselect Name from table2"""
        )
        self.assertIsInstance(block.expressions[0], SelectExpression)
        self.assertIsInstance(block.expressions[1], SelectExpression)
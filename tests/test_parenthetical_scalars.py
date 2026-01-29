from tests.utilities import read
from unittest import TestCase
from parsing.expressions.scalar_expression import ScalarExpression


class TestParentheticalScalars(TestCase):
    """Test parenthetical scalar expressions."""

    def test_parenthetical_scalar_expression(self):
        """Test parsing and tracing of parenthetical scalar expressions."""
        sql = "(A = 1)"
        scalar = ScalarExpression.consume(read(sql))
        self.assertTrue(str(scalar), '(A = 1)')
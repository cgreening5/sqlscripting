import unittest

from analysis.tracer import Node, Tracer, BinaryOperationNode, LiteralNode
from parsing.expressions.scalar_expression import ScalarExpression
from parsing.expressions.select_expression import SelectExpression
from parsing.tokenizer import Tokenizer
from tests.utilities import parse, read

class TestTracer(unittest.TestCase):
    block = parse("select 1 as Col1 from Table1")
    node = Tracer(block).trace("Col1")
    assert node.type == Node.LITERAL
    assert node.value == '1'


class TestBinaryOperationNode(unittest.TestCase):
    """Test cases for BinaryOperationNode, focusing on parenthesize_operand() logic."""

    def test_literal_nodes_no_parentheses(self):
        """Test that binary operations with literal nodes don't add unnecessary parentheses."""
        left = LiteralNode('1')
        right = LiteralNode('2')
        node = BinaryOperationNode(left, 'AND', right)
        self.assertEqual(str(node), '1 AND 2')

    def test_and_or_precedence_right_or_needs_parentheses(self):
        """Test that OR on the right of AND gets parenthesized."""
        # (1 OR 2) should be parenthesized when it's the right operand of AND
        inner = BinaryOperationNode(LiteralNode('1'), 'OR', LiteralNode('2'))
        outer = BinaryOperationNode(LiteralNode('0'), 'AND', inner)
        self.assertTrue(outer.parenthesize_operand())
        self.assertEqual(str(outer), '0 AND (1 OR 2)')

    def test_or_and_no_parentheses_for_right(self):
        """Test that AND on the right of OR doesn't get parenthesized."""
        # 1 AND 2 should NOT be parenthesized when it's the right operand of OR
        inner = BinaryOperationNode(LiteralNode('1'), 'AND', LiteralNode('2'))
        outer = BinaryOperationNode(LiteralNode('0'), 'OR', inner)
        self.assertFalse(outer.parenthesize_operand())
        self.assertEqual(str(outer), '0 OR 1 AND 2')

    def test_same_operator_no_parentheses(self):
        """Test that operations with the same operator don't add parentheses on the right."""
        # 1 AND 2 on the right of AND should not be parenthesized
        inner = BinaryOperationNode(LiteralNode('1'), 'AND', LiteralNode('2'))
        outer = BinaryOperationNode(LiteralNode('0'), 'AND', inner)
        self.assertFalse(outer.parenthesize_operand())
        self.assertEqual(str(outer), '0 AND 1 AND 2')

    def test_same_or_operator_no_parentheses(self):
        """Test that OR operations with same operator don't add parentheses on the right."""
        # 1 OR 2 on the right of OR should not be parenthesized
        inner = BinaryOperationNode(LiteralNode('1'), 'OR', LiteralNode('2'))
        outer = BinaryOperationNode(LiteralNode('0'), 'OR', inner)
        self.assertFalse(outer.parenthesize_operand())
        self.assertEqual(str(outer), '0 OR 1 OR 2')

    def test_literal_right_operand_no_parentheses(self):
        """Test that literal nodes on the right don't get parenthesized."""
        # A literal node is never a BinaryOperationNode, so parenthesize_operand returns False
        left = LiteralNode('1')
        right = LiteralNode('2')
        node = BinaryOperationNode(left, 'AND', right)
        self.assertFalse(node.parenthesize_operand())

    def test_complex_nested_expression(self):
        """Test complex nested expression: (1 AND 2) OR (3 AND 4)."""
        and1 = BinaryOperationNode(LiteralNode('1'), 'AND', LiteralNode('2'))
        and2 = BinaryOperationNode(LiteralNode('3'), 'AND', LiteralNode('4'))
        outer = BinaryOperationNode(and1, 'OR', and2)
        
        # The right operand (and2) has higher precedence (AND) than OR,
        # so it should not be parenthesized
        self.assertFalse(outer.parenthesize_operand())
        self.assertEqual(str(outer), '1 AND 2 OR 3 AND 4')

    def test_triple_nested_and_then_or(self):
        """Test: (1 AND 2) OR (3 OR 4) - where the right OR operation needs parentheses? No, OR is lower precedence."""
        and_node = BinaryOperationNode(LiteralNode('1'), 'AND', LiteralNode('2'))
        or_node = BinaryOperationNode(LiteralNode('3'), 'OR', LiteralNode('4'))
        outer = BinaryOperationNode(and_node, 'OR', or_node)
        
        # OR on the right of OR should not be parenthesized (same precedence)
        self.assertFalse(outer.parenthesize_operand())
        self.assertEqual(str(outer), '1 AND 2 OR 3 OR 4')

    def test_or_followed_by_and_on_right_no_parentheses(self):
        """Test: A OR (B AND C) - AND has higher precedence, so no parentheses needed."""
        and_node = BinaryOperationNode(LiteralNode('B'), 'AND', LiteralNode('C'))
        or_node = BinaryOperationNode(LiteralNode('A'), 'OR', and_node)
        
        # AND has higher precedence than OR, so no parentheses needed
        self.assertFalse(or_node.parenthesize_operand())
        self.assertEqual(str(or_node), 'A OR B AND C')

    def test_and_followed_by_or_on_right_needs_parentheses(self):
        """Test: A AND (B OR C) - OR has lower precedence, so parentheses needed."""
        or_node = BinaryOperationNode(LiteralNode('B'), 'OR', LiteralNode('C'))
        and_node = BinaryOperationNode(LiteralNode('A'), 'AND', or_node)
        
        # OR has lower precedence than AND, so parentheses ARE needed
        self.assertTrue(and_node.parenthesize_operand())
        self.assertEqual(str(and_node), 'A AND (B OR C)')

    def test_case_insensitive_operators(self):
        """Test that operators are case-insensitive in precedence checking."""
        # Test with lowercase operators
        or_lower = BinaryOperationNode(LiteralNode('B'), 'or', LiteralNode('C'))
        and_upper = BinaryOperationNode(LiteralNode('A'), 'AND', or_lower)
        self.assertTrue(and_upper.parenthesize_operand())
        
        # Test with mixed case
        or_mixed = BinaryOperationNode(LiteralNode('B'), 'Or', LiteralNode('C'))
        and_mixed = BinaryOperationNode(LiteralNode('A'), 'AnD', or_mixed)
        self.assertTrue(and_mixed.parenthesize_operand())

    def test_not_operator_precedence(self):
        """Test NOT operator precedence in relation to AND and OR."""
        sql = "A = 1 AND (NOT B = 2) OR C = 3"
        boolean = ScalarExpression.consume(read(sql))
        self.assertTrue(boolean.trace(None), 'A = 1 AND NOT B = 2 OR C = 3')

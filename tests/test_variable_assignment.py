import unittest

from tests.utilities import parse


class TestVariableAssignment(unittest.TestCase):

    def test_to_string(self):
        sql = "set @var = 1"
        clauses = parse(sql)
        self.assertEqual(sql, str(clauses[0]))

    def test_uppercase(self):
        sql = "set @var = 1"
        clauses = parse(sql)
        self.assertEqual("SET @var = 1", clauses[0].uppercase())


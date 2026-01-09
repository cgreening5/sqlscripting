import unittest

from tests.utilities import parse


class TestVariableAssignment(unittest.TestCase):

    def test_to_string(self):
        sql = "set @var = 1"
        self.assertEqual(sql, str(parse(sql)))

    def test_uppercase(self):
        sql = "set @var = 1"
        self.assertEqual("SET @var = 1", parse(sql).uppercase())


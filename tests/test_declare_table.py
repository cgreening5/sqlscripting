import unittest

from tests.utilities import parse


class TestDeclareTable(unittest.TestCase):

    def test_declare_table(self):
        sql = """declare @table as table(id int identity(1, 1))"""
        parsed = parse(sql)
        self.assertEqual(sql, str(parsed))
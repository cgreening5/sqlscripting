import unittest

from tests.utilities import parse

class TestTransaction(unittest.TestCase):

    def test_transaction(self):
        sql = """begin tran"""
        parse(sql)
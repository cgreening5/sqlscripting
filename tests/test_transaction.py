import unittest

from parsing.parser import Parser
from parsing.tokenizer import Tokenizer
from tests.utilities import parse

class TestTransaction(unittest.TestCase):

    def test_transaction(self):
        sql = """begin tran"""
        parse(sql)

    def test_uppercase(self):
        sql = """begin tran @tranname"""
        self.assertEqual(parse(sql).uppercase(), "BEGIN TRAN @tranname")
import unittest

from tests.utilities import parse


class TestScalarExpressionParsing(unittest.TestCase):

    def test_addition(self):
        sql = """select Column1 + ' ' + '!' from Table"""
        clauses = parse(sql)
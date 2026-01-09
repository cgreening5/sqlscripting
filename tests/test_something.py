import unittest

from tests.utilities import parse


class TestScalarExpressionParsing(unittest.TestCase):

    def test_addition(self):
        sql = "if(@@FETCH_STATUS <> -2)" \
            "   begin tran @tranname"
        self.assertEqual(
            parse(sql).uppercase(), 
            "IF(@@FETCH_STATUS <> -2)" \
            "   BEGIN TRAN @tranname"
        )
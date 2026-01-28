import unittest

from analysis.tracer import Node, Tracer
from tests.utilities import parse

class TestTracer(unittest.TestCase):
    block = parse("select 1 as Col1 from Table1")
    node = Tracer(block).trace("Col1")
    assert node.type == Node.LITERAL
    assert node.value == '1'

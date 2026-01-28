from analysis.dataservice import DataService
from analysis.resultset import ResultSet
from parsing.tokenizer import Tokenizer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parsing.expressions.block_expression import BlockExpression
    from parsing.expressions.scalar_expression import IdentifierExpression

class Node:

    LITERAL = 'LITERAL'
    COLUMN = 'COLUMN'

    def __init__(self, node_type: str, value: str):
        self.type = node_type
        self.value = value

    def __str__(self):
        if self.type == Node.LITERAL:
            return "Hardcoded value: " + self.value
        elif self.type == Node.COLUMN:
            return "Column: " + self.value
        raise NotImplementedError(f"Node type '{self.type}' not implemented.")

class Tracer:
    def __init__(self, block: 'BlockExpression', dataservice: DataService=None):
        self.block = block
        self.dataservice = dataservice

    def trace(self, column: str = None, column_index: int = None, resultset_index: int = None):
        self.resultsets: list[ResultSet] = []
        for expression in self.block.expressions:
            if expression.produces_resultset:
                self.resultsets.append(expression)
        if len(self.resultsets) == 0:
            raise ValueError("No result sets produced in the block.")
        elif len(self.resultsets) == 1:
            resultset = self.resultsets[0]
        else:
            if resultset_index is None:
                raise ValueError("Multiple result sets produced; specify which one to trace.")
            if resultset_index < 0 or resultset_index > len(self.resultsets) - 1:
                raise ValueError(f"Result set {resultset_index} is out of range; there are {len(self.resultsets)} result sets.")
            resultset = self.resultsets[resultset_index]
        columns, columns_list = self.get_columns(resultset)
        if column is not None:
            if column.lower() not in columns:
                raise ValueError(f"Column '{column}' not found in result set ({list(columns.keys())})")
            return resultset.trace(self, columns[column.lower()])
        elif column_index is not None:
            if column_index < 0 or column_index >= len(columns_list):
                raise ValueError(f"Column index {column_index} is out of range; there are {len(resultset.columns_list)} columns.")
            return resultset.trace(self, columns_list[column_index])
        else: raise ValueError("Specify either a column name or a column index to trace.")

    def get_columns(self, resultset: ResultSet):
        columns_list = resultset.columns()
        columns = {}
        for column in resultset.columns():
            from parsing.expressions.scalar_expression import ScalarExpression
            if isinstance(column, ScalarExpression) and column.has_name:
                columns[column.get_name().lower()] = column
            else:
                raise NotImplementedError(f"Not implemented: {column.__class__.__name__}. Only named scalar expressions are supported in result sets.")
        return columns, columns_list

    def trace_identifier(self, column: 'IdentifierExpression'):
        if self.dataservice and self.dataservice.get_object_type(column.uppercase()) == 'V':
            view = self.dataservice.get_view_definition(column)
            from parsing.parser import Parser
            block = Parser(Tokenizer(view).parse()).parse()
            raise NotImplementedError('No support for tracing views')
        else:
            return column.uppercase()
from analysis.dataservice import DataService
from analysis.resultset import ResultSet
from parsing.expressions.block_expression import BlockExpression
from parsing.expressions.clause import Clause
from parsing.expressions.scalar_expression import IdentifierExpression, ScalarExpression
from parsing.expressions.select_expression import SelectExpression
from parsing.parser import Parser
from parsing.tokenizer import Tokenizer


class Tracer:
    def __init__(self, block: BlockExpression, dataservice: DataService=None):
        self.block = block
        self.dataservice = dataservice

    def trace(self, column: str = None, column_index: int = None, result_set: int = None):
        self.resultsets: list[ResultSet] = []
        for expression in self.block.expressions:
            if expression.produces_resultset:
                self.resultsets.append(expression)
        if len(self.resultsets) == 0:
            raise ValueError("No result sets produced in the block.")
        elif len(self.resultsets) == 1:
            resultset = self.resultsets[0]
        else:
            if result_set is None:
                raise ValueError("Multiple result sets produced; specify which one to trace.")
            if result_set < 0 or result_set > len(self.resultsets) - 1:
                raise ValueError(f"Result set {result_set} is out of range; there are {len(self.resultsets)} result sets.")
            resultset = self.resultsets[result_set]
        columns, columns_list = self.get_columns(resultset)
        if column is not None:
            if column not in columns:
                raise ValueError(f"Column '{column}' not found in result set.")
            return ResultSetTracer(resultset).trace(columns[column])
        elif column_index is not None:
            if column_index < 0 or column_index >= len(columns_list):
                raise ValueError(f"Column index {column_index} is out of range; there are {len(resultset.columns_list)} columns.")
            return ResultSetTracer(resultset).trace(columns_list[column_index])
        else: raise ValueError("Specify either a column name or a column index to trace.")

    def get_columns(self, resultset: ResultSet):
        columns_list = resultset.columns()
        columns = {}
        for column in resultset.columns():
            if isinstance(column, ScalarExpression) and column.has_name:
                columns[column.get_name().lower()] = column
        return columns, columns_list

    def trace_identifier(self, column: IdentifierExpression):
        if self.dataservice and self.dataservice.get_object_type(column.uppercase()) == 'V':
            view = self.dataservice.get_view_definition(column)
            block = Parser(Tokenizer(view).parse()).parse()
            raise NotImplementedError('No support for tracing views')
        else:
            return column.uppercase()

class ResultSetTracer:

    def __init__(self, resultset) -> None:
        self.resultset = resultset

    def trace(self, column):
        self.resultset.trace(column)
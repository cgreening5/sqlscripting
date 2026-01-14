from analysis.resultset import ResultSet
from parsing.expressions.block_expression import BlockExpression


class Tracer:
    def __init__(self, block: BlockExpression):
        self.block = block

    def trace(self, column: str = None, column_index: int = None, result_set: int = None):
        self.resultsets: list[ResultSet] = []
        for expression in self.block.expressions:
            if expression.produces_resultset:
                self.resultsets.append(expression.get_resultset())
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
        if column is not None:
            if column not in resultset.columns:
                raise ValueError(f"Column '{column}' not found in result set.")
            return resultset.columns[column]
        elif column_index is not None:
            if column_index < 0 or column_index >= len(resultset.columns_list):
                raise ValueError(f"Column index {column_index} is out of range; there are {len(resultset.columns_list)} columns.")
            return resultset.columns_list[column_index].uppercase()
        else: raise ValueError("Specify either a column name or a column index to trace.")
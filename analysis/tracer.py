from analysis.dataservice import DataService
from analysis.resultset import ResultSet
from parsing.expressions.scalar_expression import TableIdentifierExpression
from parsing.expressions.scalar_expression import ScalarExpression, ColumnIdentifierExpression
from parsing.expressions.select_expression import SelectExpression
from parsing.tokenizer import Tokenizer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parsing.expressions.block_expression import BlockExpression

class Node:

    LITERAL = 'LITERAL'
    COLUMN = 'COLUMN'
    BINARY_OPERATION = 'BINARY_OPERATION'
    UNARY_OPERATION = 'UNARY_OPERATION'

    def __init__(self, node_type: str, value: str):
        self.type = node_type
        self.value = value

    def __str__(self):
        raise NotImplementedError(f"Node type '{self.type}' not implemented.")
    
class LiteralNode(Node):
    
    def __init__(self, value: str):
        super().__init__(Node.LITERAL, value)

    def __str__(self):
        return self.value

class UnaryOperationNode(Node):

    def __init__(self, operator: str, operand: Node):
        super().__init__(Node.UNARY_OPERATION, f'{operator} {operand}')
        self.operator = operator
        self.operand = operand

    def __str__(self):
        return f'{self.operator} {self.operand}'

class BinaryOperationNode(Node):

    def __init__(self, left: Node, operator: str, right: Node):
        super().__init__(Node.BINARY_OPERATION, f'({left} {operator} {right})')
        self.left = left
        self.operator = operator
        self.right = right
        assert self.operator is not None, "BinaryOperationNode operator cannot be None"
        assert self.left is not None, "BinaryOperationNode left operand cannot be None"
        assert self.right is not None, "BinaryOperationNode right operand cannot be None"

    def parenthesize_operand(self) -> bool:
        if isinstance(self.right, BinaryOperationNode):
            # Define operator precedence (higher number = higher precedence/tighter binding)
            precedence = {
                'OR': 1,
                'AND': 2,
                'NOT': 3,
                # Add more operators as needed
            }
            
            # Get the precedence of the current and right operators
            current_precedence = precedence.get(self.operator.upper(), 0)
            right_precedence = precedence.get(self.right.operator.upper(), 0)

            # Parenthesize if the right operator has LOWER precedence (binds less tightly)
            return right_precedence < current_precedence
        return False
        

    def __str__(self):
        left = self.left
    
        right = self.right
        if right.type not in (Node.LITERAL, Node.COLUMN):
            if self.parenthesize_operand():
                right = f'({right})'
    
        return f'{left} {self.operator} {right}'
    
class ColumnIdentifier(Node):

    def __init__(self, database: str, schema: str, table: str, column: str):
        super().__init__(Node.COLUMN, f"{database}.{schema}.{table}.{column}")
        self.database = database
        self.schema = schema
        self.table = table
        self.column = column

    def __str__(self):
        return '.'.join(identifier for identifier in (self.database, self.schema, self.table, self.column) if identifier is not None)

class Tracer:
    def __init__(self, block: 'BlockExpression', dataservice: DataService=None):
        self.block = block
        self.dataservice = dataservice

    def trace(self, column: str = None, column_index: int = None, resultset_index: int = None) -> 'ScalarExpression':
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

    def trace_column_identifier(self, identifier: ColumnIdentifierExpression):
        if self.dataservice and self.dataservice.get_object_type(identifier.uppercase()) == 'V':
            view = self.dataservice.get_view_definition(identifier)
            from parsing.parser import Parser
            block = Parser(Tokenizer(view).parse()).parse()
            raise NotImplementedError('No support for tracing views')
        else:
            return identifier.uppercase()
        
    def trace_table_identifier(self, identifier: TableIdentifierExpression):
        if identifier.table.token.value.startswith("#"):
            source = self.find_temp_table(identifier.table.token.value)
            print(source.lowercase())
        elif self.dataservice and self.dataservice.get_object_type(identifier.uppercase()) == 'V':
            view = self.dataservice.get_view_definition(identifier.table.token.value)
            from parsing.parser import Parser
            block = Parser(Tokenizer(view).parse()).parse()
            raise NotImplementedError('No support for tracing views')
        else:
            return identifier.uppercase()
        
    def find_temp_table(self, identifier: str):
        for expression in self.block.expressions:
            if isinstance(expression, SelectExpression) and expression.into != None:
                if expression.into.dest.token.value.lower() == identifier.lower():
                    return expression
from parsing.expressions.scalar_expression import ScalarExpression, AliasedScalarIdentifierExpression

class ResultSet:

    def __init__(self, columns: list[ScalarExpression | AliasedScalarIdentifierExpression]):
        print("ResultSet columns:", columns)
        self.columns_list = columns
        self.columns = {}
        for column in columns:
            if isinstance(column, ScalarExpression) and column.has_name:
                self.columns[column.get_name().lower()] = column
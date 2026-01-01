from parsing.expressions.clause import Clause
from parsing.expressions.declare_expression import VariableExpression
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader
from parsing.tokenizer import Token

class ArgumentsListExpression(Clause):

    def __init__(self, open_parenthesis: TokenContext, comma_separated_arguments: list[TokenContext | Clause], closing_parenthesis: TokenContext):
        from parsing.expressions.scalar_expression import ScalarExpression
        super().__init__([open_parenthesis] + comma_separated_arguments + [closing_parenthesis])
        self.arguments = []
        assert len(comma_separated_arguments) == 0 or len(comma_separated_arguments) % 2 == 1
        for i, token in enumerate(comma_separated_arguments):
            if i % 2 == 0:
                self.arguments.append(token)
                assert isinstance(token, ScalarExpression) \
                    or isinstance(token, VariableExpression), \
                    f"Found invalid expression {token} ({token.__class__.__name__}) in {self.arguments}"
            else:
                assert token.token.value == ','


    @classmethod
    def consume(cls, reader: Reader):
        
        from parsing.expressions.scalar_expression import ScalarExpression
        open_parenthesis = reader.expect_symbol('(')
        comma_separated_arguments = []
        while reader.curr_value_lower != ')':
            comma_separated_arguments.append(ScalarExpression.consume(reader))
            if reader.curr_value_lower == ',':
                comma_separated_arguments.append(reader.expect_symbol(','))
                assert reader.curr_value_lower != ')'
        closing_parenthesis = reader.expect_symbol(')')
        return ArgumentsListExpression(open_parenthesis, comma_separated_arguments, closing_parenthesis)
            
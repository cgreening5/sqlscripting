from parsing.expressions.arguments_list import ArgumentsListExpression
from parsing.expressions.declare_expression import VariableExpression
from parsing.tokenizer import Token
from typing import Self
from parsing.expressions.clause import Clause
from parsing.expressions.datatype import DataTypeClause
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader

class ScalarExpression(Clause):

    def __init__(self, tokens: list[TokenContext|Clause]):
        super().__init__(list(filter(lambda t: t, tokens)))

    @classmethod
    def consume(cls, reader: Reader) -> Self:
        left = ScalarExpression._consume(reader)
        if reader.curr_value_lower in ['+', '-']:
            return ScalarExpression.consume_plus_or_minus_operator(reader, left)
        else:
            return left
            
    @classmethod 
    def consume_plus_or_minus_operator(cls, reader: Reader, left: Self) -> Self:
        while reader.curr_value_lower in ['-', '+']:
            operator = reader.expect_symbol(reader.curr_value_lower)
            right = ScalarExpression._consume(reader)
            return AdditionSubtractionExpression(left, operator, right)    
        
    @classmethod
    def _consume(cls, reader: Reader) -> Self:
        
        if reader.curr.type == Token.QUOTED_IDENTIFIER:
            return IdentifierExpression.consume(reader)
        elif reader.curr.type == Token.WORD:
            if reader.curr.value.lower() == 'cast':
                return CastExpression.consume(reader)
            elif reader.curr.value.lower() == 'concat':
                return ConcatExpression.consume(reader)
            elif reader.curr.value.lower() == 'right':
                return RightExpression.consume(reader)
            elif reader.curr.value.lower() == 'case':
                return CaseExpression.consume(reader)
            elif reader.curr.value.lower() == 'substring':
                return SubstringExpression.consume(reader)
            elif reader.curr_value_lower == 'len':
                return LenExpression.consume(reader)
            elif reader.curr_value_lower == 'replace':
                return ReplaceExpression.consume(reader)
            elif reader.curr_value_lower == 'format':
                return FormatExpression.consume(reader)
            elif reader.curr_value_lower == 'year':
                return YearExpression.consume(reader)
            elif reader.curr_value_lower == 'getdate':
                return GetDateExpression.consume(reader)
            else:
                return IdentifierExpression.consume(reader)
        elif reader.curr.type == Token.NUMBER:
            return NumberLiteralExpression.consume(reader)
        elif reader.curr.type == Token.SYMBOL:
            if reader.curr_value_lower == '(':
                return ParentheticalExpression.consume(reader)
        elif reader.curr.type == Token.VARIABLE:
            return VariableExpression.consume(reader)
        raise ValueError(f'Invalid token type {reader.curr.type} ({reader.curr_value_lower})')

class GetDateExpression(ScalarExpression):

    def __init__(self, getdate, opening_parenthesis, closing_parenthesis):
        super().__init__([getdate, opening_parenthesis, closing_parenthesis])

    @staticmethod
    def consume(reader: Reader):
        return GetDateExpression(
            reader.expect_word('getdate'),
            reader.expect_symbol('('),
            reader.expect_symbol(')')
        )

class ParentheticalExpression(ScalarExpression):

    def __init__(self, opening_parenthesis, expression, closing_parenthesis):
        super().__init__([opening_parenthesis, expression, closing_parenthesis])
        self.expression = expression

    @staticmethod
    def consume(reader: Reader):
        from parsing.expressions.select_expression import SelectExpression
        opening_parenthesis = reader.expect_symbol('(')
        if reader.curr_value_lower == 'select':
            expression = SelectExpression.consume(reader)
            assert len(expression.projection) == 1
        else:
            expression = ScalarExpression.consume(reader)
        return ParentheticalExpression(
            opening_parenthesis,
            expression,
            reader.expect_symbol(')')
        )

class YearExpression(ScalarExpression):

    def __init__(self, year: TokenContext, args: ArgumentsListExpression):
        super().__init__([year, args])
        [self.year] = args.arguments

    @staticmethod
    def consume(reader: Reader):
        year = reader.expect_word('year')
        args = ArgumentsListExpression.consume(reader)
        return YearExpression(year, args)
        
class FormatExpression(ScalarExpression):

    def __init__(self, format: TokenContext, args: ArgumentsListExpression):
        super().__init__([format, args])
        assert len(args) == 3
        assert isinstance(args[0], ScalarExpression)
        self.args = args.arguments

    @classmethod
    def consume(cls, reader) -> Self:
        format = reader.expect_word('format')
        args = ArgumentsListExpression.consume(reader)
        
class AdditionSubtractionExpression(ScalarExpression):

    def __init__(self, left: ScalarExpression, operator: TokenContext, right: ScalarExpression):
        super().__init__([left, operator, right])
        self.left = left
        self.operator = operator
        self.right = right

class LenExpression(ScalarExpression):
    def __init__(self, len, open_paren: TokenContext, expression: ScalarExpression, closed_paren: TokenContext):
        super().__init__([len, open_paren, expression, closed_paren])

    @classmethod
    def consume(cls, reader):
        len = reader.expect_word('len')
        open_paren = reader.expect_symbol('(')
        expression = ScalarExpression.consume(reader)
        closing_paren = reader.expect_symbol(')')
        return LenExpression(len, open_paren, expression, closing_paren)

class NumberLiteralExpression(ScalarExpression):
    def __init__(self, number):
        super().__init__([number])

    @classmethod
    def consume(cls, reader):
        return NumberLiteralExpression(reader.expect(Token.NUMBER))

class IdentifierExpression(ScalarExpression):
    def __init__(self, period_separated_identifiers: list[TokenContext]):
        assert len(period_separated_identifiers) in (1, 3, 5)
        super().__init__(period_separated_identifiers)
        self.name = period_separated_identifiers[-1]
        self.table = None
        self.schema = None
        if len(period_separated_identifiers) >= 3:
            self.table = period_separated_identifiers[2]
        if len(period_separated_identifiers) == 5:
            self.schema = period_separated_identifiers[4]

    @classmethod
    def consume(cls, reader: Reader) -> Self:
        assert reader.curr.type in [Token.QUOTED_IDENTIFIER, Token.WORD, Token.VARIABLE]
        identifiers = [reader.expect(reader.curr.type)]
        while reader.curr_value_lower == '.':
            identifiers.append(reader.expect_symbol('.'))
            assert reader.curr.type in [Token.QUOTED_IDENTIFIER, Token.WORD]
            identifiers.append(reader.expect(reader.curr.type))
        return IdentifierExpression(identifiers)
            

class ReplaceExpression(ScalarExpression):
    def __init__(self, replace: TokenContext, arguments: ArgumentsListExpression):
        super().__init__([replace, arguments])
        [self.string, self.old_string, self.new_string] = arguments.arguments

    @classmethod
    def consume(cls, reader: Reader):
        replace = reader.expect_word('replace')
        arguments = ArgumentsListExpression.consume(reader)

        return ReplaceExpression(replace, arguments)

class RightExpression(ScalarExpression):
    def __init__(
        self,
        right: TokenContext,
        open_parenthesis: TokenContext,
        inner_expression: ScalarExpression,
        comma: TokenContext,
        number: TokenContext,
        closing_parenthesis: TokenContext
    ):
        super().__init__([right, open_parenthesis, inner_expression, closing_parenthesis ])
        self.inner_expression = inner_expression

    @classmethod
    def consume(cls, reader: Reader) -> Self:        
        right = reader.expect_word('right')
        open_parenthesis = reader.expect_symbol('(')
        inner_expression = ScalarExpression.consume(reader)
        comma = reader.expect_symbol(',')
        number = reader.expect(Token.NUMBER)
        right_parenthesis = reader.expect_symbol(')')
        return RightExpression(right, open_parenthesis, inner_expression, comma, number, right_parenthesis)

class CastExpression(ScalarExpression):
    def __init__(
        self, 
        cast: TokenContext, 
        open_parenthesis: TokenContext, 
        val: TokenContext, 
        _as: TokenContext, 
        datatype: DataTypeClause,
        closing_parenthesis: TokenContext
    ):
        super().__init__([cast, open_parenthesis, val, _as, datatype])
        self.datatype = datatype
        self.val = val

    @classmethod
    def consume(cls, reader: Reader) -> Self:
        cast = reader.expect_word('cast')
        open_parenthesis = reader.expect_symbol('(')
        scalar = ScalarExpression.consume(reader)
        _as = reader.expect_word('as')
        datatype = reader.expect_word()
        closing_parentheses = reader.expect_symbol(')')
        return CastExpression(cast, open_parenthesis, scalar, _as, datatype, closing_parentheses)
        

class ConcatExpression(ScalarExpression):
    def __init__(
        self,
        concat: TokenContext,
        open_parenthesis: TokenContext,
        comma_separated_expressions: list[TokenContext | ScalarExpression],
        closing_parenthesis: TokenContext
    ):
        self.expressions: list[ScalarExpression] = filter(lambda e: e.value != 'comma',  comma_separated_expressions)
        super().__init__([concat, open_parenthesis, *comma_separated_expressions, closing_parenthesis])

    @classmethod
    def consume(cls, reader: Reader) -> Self:
        concat = reader.expect_word('concat')
        open_parenthesis = reader.expect_symbol('(')
        terms = []
        while True:
            terms.append(ScalarExpression.consume(reader))
            if reader.curr.value == ',':
                terms.append(reader.expect_symbol(','))
            else:
                closing_parenthesis = reader.expect_symbol(')')
                return ConcatExpression(concat, open_parenthesis, terms, closing_parenthesis)

class BooleanExpression(ScalarExpression):

    @staticmethod
    def consume(reader: Reader) -> Self:
        return BooleanExpression._consume_maybe_or(reader)
        
    @staticmethod
    def _consume_maybe_or(reader:Reader):
        left = BooleanExpression._consume_maybe_and(reader)
        while reader.curr_value_lower == 'or':
            left = BooleanOperationExpression(
                left, 
                reader.expect_word('or'), 
                BooleanExpression._consume_maybe_and(reader))
        return left
            
    @staticmethod
    def _consume_maybe_and(reader: Reader):
        left = BooleanExpression._consume(reader)
        while reader.curr_value_lower == 'and':
            left = BooleanOperationExpression(
                left, 
                reader.expect_word('and'), 
                BooleanExpression._consume(reader))
        return left

    @staticmethod
    def _consume(reader: Reader):
        if reader.curr_value_lower == 'exists':
            return ExistsExpression.consume(reader)
        left = ScalarExpression.consume(reader)
        if reader.curr_value_lower in ['=', '<', '>']:
            comparator = BooleanOperatorExpression.consume(reader)
            right = ScalarExpression.consume(reader)
            return EqualsExpression(left, comparator, right)
        elif reader.curr_value_lower == 'in':
            _in = reader.expect_word('in')
            args = ArgumentsListExpression.consume(reader)
            return InExpression(left, _in, args)
        else:
            return left
        
class InExpression(BooleanExpression):

    def __init__(self, val: ScalarExpression, _in: TokenContext, args: ArgumentsListExpression):
        super().__init__([val, _in, args])
        self.val = val
        self._in = _in
        self.args = args
        
class ExistsExpression(BooleanExpression):

    def __init__(self, exists, nested_select):
        super().__init__([exists, nested_select])
        self.nested_select = nested_select

    @staticmethod
    def consume(reader):
        return ExistsExpression(
            reader.expect_word('exists'),
            ParentheticalExpression.consume(reader)
        )
        
class BooleanOperatorExpression(Clause):

    def __init__(self, operator):
        super().__init__([operator])

    @staticmethod
    def consume(reader: Reader):
        patterns = [
            '=',
            '>',
            '<'
            '<>',
            '>=',
            '<=',
            '!=',
        ]
        match = reader.expect_from_symbols(patterns)
        if match:
            return BooleanOperatorExpression(match)
        
        
class BooleanOperationExpression(BooleanExpression):

    def __init__(self, left, operator, right):
        super().__init__([left, operator, right])
        self.left = left
        self.operator = operator
        self.right = right

class CaseWhenExpression(Clause):

    def __init__(self, when: TokenContext, predicate: BooleanExpression, then: TokenContext, result: ScalarExpression):
        super().__init__([when, predicate, then, result])
        self.predicate = predicate
        self.result = result

    @classmethod
    def consume(cls, reader: Reader) -> Self:
            when = reader.expect_word('when')
            predicate = BooleanExpression.consume(reader)
            then = reader.expect_word('then')
            result = ScalarExpression.consume(reader)
            return CaseWhenExpression(when, predicate, then, result)

class CaseExpression(ScalarExpression):

    def __init__(self, case: TokenContext, cases: list[CaseWhenExpression], end: TokenContext):
        super().__init__([case, *cases, end])

    @classmethod
    def consume(cls, reader: Reader) -> Self:
        case = reader.expect_word('case')
        token = reader.curr.value
        cases: list[CaseWhenExpression] = []
        while True:
            cases.append(CaseWhenExpression.consume(reader))
            if reader.curr_value_lower == 'end':
                end = reader.expect_word('end')
                return CaseExpression(case, cases, end)

class EqualsExpression(BooleanExpression):

    def __init__(self, left, equals, right):
        super().__init__([left, equals, right])
        self.left = left
        self.right = right
    
class SubstringExpression(ScalarExpression):

    def __init__(
            self, 
            substring: TokenContext, 
            open_parentheses: TokenContext,
            expression: ScalarExpression,
            start: ScalarExpression,
            end: ScalarExpression=None):
        super().__init__([substring, open_parentheses, expression, start])
        if end:
            super.__init__([substring, open_parentheses, expression, start, end])

    @classmethod
    def consume(cls, reader):
        substring = reader.expect_word('substring')
        comma_seperated_args = reader.expect_args(
            ScalarExpression.consume,
            ScalarExpression.consume,
            ScalarExpression.consume
        )

class AliasedScalarExpression(ScalarExpression):

    def __init__(self, expression, _as, alias):
        super().__init__([expression, _as, alias])
        self.expression = expression
        self.alias = alias
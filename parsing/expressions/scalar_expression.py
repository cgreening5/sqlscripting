from analysis.tracer import BinaryOperationNode, ColumnIdentifier, LiteralNode, Node
from parsing.expressions.arguments_list import ArgumentsListExpression
from parsing.expressions.declare_expression import VariableExpression
from parsing.tokenizer import Token
from typing import Self
from parsing.expressions.clause import Clause
from parsing.expressions.datatype import DataTypeClause
from parsing.expressions.token_context import TokenContext
from parsing.reader import Reader

class ScalarExpression(Clause):

    def __init__(self, type: str, tokens: list[TokenContext|Clause]):
        super().__init__(list(filter(lambda t: t, tokens)))
        self.type = type
        self.has_name = False

    def get_name(self) -> str:
        raise NotImplementedError()

    def trace(self, context) -> str:
        raise NotImplementedError(self.__class__.__name__ + " does not implement trace method")

    @staticmethod
    def consume(reader: Reader):
        return ScalarExpression.consume_possible_or(reader)
    
    @staticmethod
    def consume_possible_or(reader: Reader):
        left = ScalarExpression.consume_possible_and(reader)
        while reader.curr_value_lower == 'or':
            left = BooleanOperationExpression(
                left, 
                reader.expect_word('or'), 
                ScalarExpression.consume_possible_and(reader))
        return left
    
    @staticmethod
    def consume_possible_and(reader: Reader):
        left = ScalarExpression.consume_possible_comparison(reader)
        while reader.curr_value_lower == 'and':
            left = BooleanOperationExpression(
                left, 
                reader.expect_word('and'), 
                ScalarExpression.consume_possible_comparison(reader))
        return left

    @staticmethod
    def consume_possible_comparison(reader: Reader):
        left = ScalarExpression.consume_possible_addition_or_subtraction(reader)
        if reader.curr_value_lower == 'is':
            left =  IsExpression(
                left,
                reader.expect_word('is'),
                reader.consume_optional_word('not'),
                ScalarExpression.consume(reader)
            )
        else: 
            boolean_operator = reader.consume_symbol_from([
                '=', '!=', '<', '>',
                '<>', '<=', '>='
            ])
            if boolean_operator:
                left = BooleanOperationExpression(
                    left,
                    boolean_operator,
                    ScalarExpression.consume(reader)
                )
            elif reader.curr_value_lower in ['in', 'not', 'like']:
                _not = reader.consume_optional_word('not')
                if reader.curr_value_lower == 'in':
                    _in = reader.expect_word('in')
                    pos = reader._position
                    reader.expect_symbol('(')
                    if reader.curr_value_lower == 'select':
                        reader._position = pos
                        expression = ParentheticalExpression.consume(reader)
                    else:
                        reader._position = pos
                        expression = ArgumentsListExpression.consume(reader)
                    left = InExpression(
                        left,
                        _not,
                        _in,
                        expression
                    )
                else:
                    left = LikeExpression(
                        left,
                        _not,
                        reader.expect_word('like'),
                        ScalarExpression.consume(reader),
                    )
        assert isinstance(left, ScalarExpression) \
            or isinstance(left, VariableExpression), \
                f'Invalid expression: {left.__class__.__name__}'
        return left

    @staticmethod
    def consume_possible_addition_or_subtraction(reader: Reader) -> Self:
        left = ScalarExpression._consume(reader)
        while reader.curr_value_lower in ['+', '-']:
            left =  AdditionSubtractionExpression(
                left,
                reader.expect_symbol(reader.curr_value_lower),
                ScalarExpression._consume(reader)
            )
        return left
        
    @classmethod
    def _consume(cls, reader: Reader) -> Self:
        if reader.curr.type == Token.QUOTED_IDENTIFIER:
            return ColumnIdentifierExpression.consume(reader)
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
            elif reader.curr_value_lower == 'scope_identity':
                return ScopeIdentityExpression.consume(reader)
            elif reader.curr_value_lower == 'abs':
                return AbsExpression.consume(reader)
            elif reader.curr_value_lower == 'max':
                return MaxExpression.consume(reader)
            elif reader.curr_value_lower == 'object_id':
                return ObjectIdExpression.consume(reader)
            elif reader.curr_value_lower == 'isnull':
                return IsNullExpression.consume(reader)
            elif reader.curr_value_lower == 'exists':
                return ExistsExpression.consume(reader)
            else:
                return ColumnIdentifierExpression.consume(reader)
        elif reader.curr.type == Token.NUMBER:
            return NumberLiteralExpression.consume(reader)
        elif reader.curr.type == Token.SYMBOL:
            if reader.curr_value_lower == '(':
                return ParentheticalScalarExpression.consume(reader)
            if reader.curr_value_lower == '-':
                return NegativeExpression.consume(reader)
        elif reader.curr.type == Token.VARIABLE:
            return VariableExpression.consume(reader)
        raise ValueError(f'Invalid token type {reader.curr.type} ({reader.curr_value_lower})')

class NegativeExpression(ScalarExpression):

    def __init__(self, minus, expression):
        super().__init__('number', [minus, expression])

    @staticmethod
    def consume(reader: Reader):
        return NegativeExpression(
            reader.expect_symbol('-'),
            ScalarExpression.consume(reader),
        )
    
class ScopeIdentityExpression(ScalarExpression):

    def __init__(self, scope_identity, opening_parentheses, closing_parentheses):
        super().__init__('number', [scope_identity, opening_parentheses, closing_parentheses])

    @staticmethod
    def consume(reader: Reader):
        return ScopeIdentityExpression(
            reader.expect_word('scope_identity'),
            reader.expect_symbol('('),
            reader.expect_symbol(')')
        )

class GetDateExpression(ScalarExpression):

    def __init__(self, getdate, opening_parenthesis, closing_parenthesis):
        super().__init__('date', [getdate, opening_parenthesis, closing_parenthesis])

    @staticmethod
    def consume(reader: Reader):
        return GetDateExpression(
            reader.expect_word('getdate'),
            reader.expect_symbol('('),
            reader.expect_symbol(')')
        )

class ParentheticalExpression(Clause):

    def __init__(self, opening_parenthesis, expression, closing_parenthesis):
        super().__init__([opening_parenthesis, expression, closing_parenthesis])
        self.expression = expression

    @staticmethod
    def consume(reader: Reader):
        from parsing.expressions.select_expression import SelectExpression
        opening_parenthesis = reader.expect_symbol('(')
        if reader.curr_value_lower == 'select':
            expression = SelectExpression.consume(reader)
        else:
            expression = ScalarExpression.consume(reader)
        return ParentheticalExpression(
            opening_parenthesis,
            expression,
            reader.expect_symbol(')')
        )

class ParentheticalScalarExpression(ScalarExpression):

    def __init__(self, paranthetical_expression: ParentheticalExpression):
        from parsing.expressions.select_expression import SelectExpression
        if isinstance(paranthetical_expression.expression, SelectExpression):
            assert len(paranthetical_expression.expression.projection) == 1, \
                "Subquery in paranthetical scalar expression must return exactly one column"
            type = paranthetical_expression.expression.projection[0].type
        else:
            assert isinstance(paranthetical_expression.expression, ScalarExpression), \
                "Paranthetical expression must contain a scalar expression"
            type = paranthetical_expression.expression.type
        super().__init__(type, [paranthetical_expression])
        self.paranthetical_expression = paranthetical_expression

    @staticmethod
    def consume(reader: Reader):
        return ParentheticalScalarExpression(
            ParentheticalExpression.consume(reader)
        )

class YearExpression(ScalarExpression):

    def __init__(self, year: TokenContext, args: ArgumentsListExpression):
        super().__init__('number', [year, args])
        [self.year] = args.arguments

    @staticmethod
    def consume(reader: Reader):
        year = reader.expect_word('year')
        args = ArgumentsListExpression.consume(reader)
        return YearExpression(year, args)
        
class FormatExpression(ScalarExpression):

    def __init__(self, format: TokenContext, args: ArgumentsListExpression):
        super().__init__('text', [format, args])
        [self.expression, self.format_string] = args.arguments

    @staticmethod
    def consume(reader) -> Self:
        format = reader.expect_word('format')
        args = ArgumentsListExpression.consume(reader)
        return FormatExpression(format, args)
        
class AdditionSubtractionExpression(ScalarExpression):

    def __init__(self, left: ScalarExpression, operator: TokenContext, right: ScalarExpression):
        super().__init__('number', [left, operator, right])
        self.left = left
        self.operator = operator
        self.right = right

    def trace(self, context):
        return BinaryOperationNode(
            self.left.trace(context),
            self.operator.token.value,
            self.right.trace(context)
        )

class LenExpression(ScalarExpression):
    def __init__(self, len, open_paren: TokenContext, expression: ScalarExpression, closed_paren: TokenContext):
        super().__init__('number', [len, open_paren, expression, closed_paren])

    @classmethod
    def consume(cls, reader):
        len = reader.expect_word('len')
        open_paren = reader.expect_symbol('(')
        expression = ScalarExpression.consume(reader)
        closing_paren = reader.expect_symbol(')')
        return LenExpression(len, open_paren, expression, closing_paren)

class NumberLiteralExpression(ScalarExpression):
    def __init__(self, number):
        super().__init__('number', [number])
        self.number = number

    def trace(self, _) -> str:
        return LiteralNode(self.number.token.value)

    @staticmethod
    def consume(reader):
        return NumberLiteralExpression(reader.expect(Token.NUMBER))

class IdentifierExpression(ScalarExpression):

    @classmethod
    def _consume_identifiers(cls, reader: Reader) -> Self:
        identifier_token_types = [Token.QUOTED_IDENTIFIER, Token.WORD, Token.VARIABLE, Token.TEMP_TABLE]
        assert reader.curr.type in identifier_token_types
        identifiers = []
        while True:
            if reader.curr_value_lower == '*':
                identifiers.append(reader.expect_symbol('*'))
                break
            identitier = reader.expect_any_of(identifier_token_types)
            if identitier.type == Token.WORD:
                identitier.type = Token.IDENTIFIER
            identifiers.append(identitier)
            if reader.curr_value_lower == '.':
                identifiers.append(reader.expect_symbol('.'))
            else:
                break    
        return identifiers


class ColumnIdentifierExpression(ScalarExpression):
    def __init__(self, database, comma1, schema, comma2, table, comma3, column):
        super().__init__('any', [database, comma1, schema, comma2, table, comma3, column])
        self.database = database
        self.schema = schema
        self.table = table
        self.column = column
        self.has_name = True

    def get_name(self):
        return self.column.token.value

    @staticmethod
    def from_parts(database: TokenContext | None, schema: TokenContext | None, table: TokenContext | None, column: TokenContext) -> Self:
        return ColumnIdentifierExpression(
            database,
            TokenContext(Token('.', Token.SYMBOL), []) if database else None,
            schema,
            TokenContext(Token('.', Token.SYMBOL), []) if schema else None,
            table,
            TokenContext(Token('.', Token.SYMBOL), []) if table else None,
            column
        )

    def trace(self, context):
        aliased_table = TableIdentifierExpression.from_parts(self.database, self.schema, self.table)
        if self.table:
            table = context.resolve_table_identifier(aliased_table)
            return ColumnIdentifier(
                table.database.token.value if table.database else None, 
                table.schema.token.value if table.schema else None,
                table.table.token.value if table.table else None,
                self.column.token.value
            )
        else:
            return ColumnIdentifier(
                None, None, None,
                self.column.token.value
            )

    @classmethod
    def consume(cls, reader: Reader) -> Self:
        identifier_token_types = [Token.QUOTED_IDENTIFIER, Token.WORD, Token.VARIABLE, Token.TEMP_TABLE]
        assert reader.curr.type in identifier_token_types
        identifiers = []
        while True:
            if reader.curr_value_lower == '*':
                identifiers.append(reader.expect_symbol('*'))
                break
            identifier = reader.expect_any_of(identifier_token_types)
            if identifier.type == Token.WORD:
                identifier.type = Token.IDENTIFIER
            identifiers.append(identifier)
            if reader.curr_value_lower == '.':
                identifiers.append(reader.expect_symbol('.'))
            else:
                break
        identifiers = [None] * (7 - len(identifiers)) + identifiers
        return ColumnIdentifierExpression(*identifiers)

class TableIdentifierExpression(Clause):

    def __init__(self, database: TokenContext | None, period1, schema: TokenContext | None, period2, table: TokenContext):
        super().__init__([database, period1, schema, period2, table])
        self.database = database
        self.schema = schema
        self.table = table

    def from_parts(database: TokenContext | None, schema: TokenContext | None, table: TokenContext) -> Self:
        return TableIdentifierExpression(
            database,
            TokenContext(Token.SYMBOL, '.') if database else None,
            schema,
            TokenContext(Token.SYMBOL, '.') if schema else None,
            table
        )
    
    @classmethod
    def consume(cls, reader: Reader) -> Self:
        identifier_token_types = [Token.QUOTED_IDENTIFIER, Token.WORD, Token.VARIABLE, Token.TEMP_TABLE]
        assert reader.curr.type in identifier_token_types
        identifiers = []
        while True:
            if reader.curr_value_lower == '*':
                identifiers.append(reader.expect_symbol('*'))
                break
            identifier = reader.expect_any_of(identifier_token_types)
            if identifier.type == Token.WORD:
                identifier.type = Token.IDENTIFIER
            identifiers.append(identifier)
            if reader.curr_value_lower == '.':
                identifiers.append(reader.expect_symbol('.'))
            else:
                break
        identifiers = [None] * (5 - len(identifiers)) + identifiers
        return TableIdentifierExpression(*identifiers)

class ReplaceExpression(ScalarExpression):
    def __init__(self, replace: TokenContext, arguments: ArgumentsListExpression):
        super().__init__('text', [replace, arguments])
        [self.string, self.pattern, self.new_string] = arguments.arguments

    @staticmethod
    def consume(reader: Reader):
        replace = reader.expect_word('replace')
        arguments = ArgumentsListExpression.consume(reader)

        return ReplaceExpression(replace, arguments)

    def trace(self, tracer):
        return f'REPLACE({self.string.trace(tracer), self.pattern.trace(tracer), self.new_string.trace(tracer)})'

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
        super().__init__('text', [right, open_parenthesis, inner_expression, closing_parenthesis])
        self.inner_expression = inner_expression

    @staticmethod
    def consume(reader: Reader) -> Self:        
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
        super().__init__(datatype.type, [cast, open_parenthesis, val, _as, datatype])
        self.datatype = datatype
        self.val = val

    @classmethod
    def consume(cls, reader: Reader) -> Self:
        cast = reader.expect_word('cast')
        open_parenthesis = reader.expect_symbol('(')
        scalar = ScalarExpression.consume(reader)
        _as = reader.expect_word('as')
        datatype = DataTypeClause.consume(reader)
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
        super().__init__('text', [concat, open_parenthesis, *comma_separated_expressions, closing_parenthesis])

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

    def __init__(self, tokens):
        super().__init__('boolean', tokens)

class IsExpression(BooleanExpression):

    def __init__(self, left, _is, _not, right):
        super().__init__([left, _is, _not, right])
        self.left = left
        self.right = right
        self._not = _not

class LikeExpression(ScalarExpression):

    def __init__(self, left, _not, like, right):
        super().__init__('boolean', [left, _not, like, right])
        self.left = left
        self._not = _not
        self.right = right

class InExpression(BooleanExpression):

    def __init__(
            self, 
            val: ScalarExpression, 
            _not: TokenContext,
            _in: TokenContext, 
            args: ArgumentsListExpression
        ):
        super().__init__([val, _not, _in, args])
        self.val = val
        self._in = _not == None
        self.args = args
        
class ExistsExpression(BooleanExpression):

    def __init__(self, exists, nested_select):
        super().__init__([exists, nested_select])
        self.nested_select = nested_select

    @staticmethod
    def consume(reader):
        return ExistsExpression(
            reader.expect_word('exists'),
            ParentheticalScalarExpression.consume(reader)
        )
        
class BooleanOperatorExpression(Clause):

    def __init__(self, operator: TokenContext):
        super().__init__([operator])
        self.operator = operator

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
        match = reader.consume_symbol_from(patterns)
        if match:
            return BooleanOperatorExpression(match)
        
        
class BooleanOperationExpression(BooleanExpression):

    def __init__(self, left: ScalarExpression, operator: BooleanOperatorExpression, right: ScalarExpression):
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
            predicate = ScalarExpression.consume(reader)
            assert predicate.type == 'boolean', "CASE WHEN predicate must be a boolean expression"
            then = reader.expect_word('then')
            result = ScalarExpression.consume(reader)
            return CaseWhenExpression(when, predicate, then, result)

class DefaultCaseExpression(Clause):

    def __init__(self, default: TokenContext, result: ScalarExpression):
        super().__init__([default, result])
        self.result = result

    @staticmethod
    def consume(reader: Reader):
        assert reader.curr_value_lower in ('else', 'default')
        return DefaultCaseExpression(
            reader.expect_word(),
            ScalarExpression.consume(reader)
        )

class CaseExpression(ScalarExpression):

    def __init__(self, case: TokenContext, cases: list[CaseWhenExpression], default: DefaultCaseExpression, end: TokenContext):
        super().__init__(None, [case, *cases, end])
        self.cases = cases
        self.default = default

    @classmethod
    def consume(cls, reader: Reader) -> Self:
        case = reader.expect_word('case')
        token = reader.curr.value
        cases: list[CaseWhenExpression] = []
        default = None
        while True:
            cases.append(CaseWhenExpression.consume(reader))
            if reader.curr_value_lower in ('else', 'default'):
                default = DefaultCaseExpression.consume(reader)
                assert reader.curr_value_lower == 'end'
            if reader.curr_value_lower == 'end':
                end = reader.expect_word('end')
                return CaseExpression(case, cases, default, end)

class ComparisonExpression(BooleanExpression):

    def __init__(self, left: ScalarExpression, operation: BooleanOperatorExpression, right: ScalarExpression):
        super().__init__([left, operation, right])
        self.left = left
        self.operation = operation
        self.right = right
    
class SubstringExpression(ScalarExpression):

    def __init__(
            self, 
            substring: TokenContext, 
            open_parentheses: TokenContext,
            expression: ScalarExpression,
            start: ScalarExpression,
            end: ScalarExpression=None):
        super().__init__('text', [substring, open_parentheses, expression, start, end])

    @classmethod
    def consume(cls, reader):
        substring = reader.expect_word('substring')
        comma_seperated_args = reader.expect_args(
            ScalarExpression.consume,
            ScalarExpression.consume,
            ScalarExpression.consume
        )

class AbsExpression(ScalarExpression):

    def __init__(self, abs: TokenContext, args: ArgumentsListExpression):
        super().__init__('number', [abs, args])
        [self.arg] = args.arguments
    
    @staticmethod
    def consume(reader: Reader):
        return AbsExpression(
            reader.expect_word('abs'),
            ArgumentsListExpression.consume(reader)
        )
    
class MaxExpression(ScalarExpression):

    def __init__(self, max: TokenContext, args: ArgumentsListExpression):
        [self.arg] = args.arguments
        assert isinstance(self.arg, ScalarExpression), "MaxExpression argument must be a ScalarExpression"
        super().__init__(self.arg.type, [max, args])

    @staticmethod
    def consume(reader: Reader):
        return MaxExpression(
            reader.expect_word('max'),
            ArgumentsListExpression.consume(reader)
        )

class ObjectIdExpression(ScalarExpression):

    def __init__(self, object_id: TokenContext, arg: ArgumentsListExpression):
        super().__init__('number', [object_id, arg])
        [self.name] = arg.arguments

    @staticmethod 
    def consume(reader: Reader):
        return ObjectIdExpression(
            reader.expect_word('object_id'),
            ArgumentsListExpression.consume(reader),
        )

class IsNullExpression(ScalarExpression):

    def __init__(self, isnull, args: ArgumentsListExpression):
        [self.expression, self.coalescing] = args.arguments
        super().__init__(self.expression.type, [isnull, args])

    @staticmethod
    def consume(reader: Reader):
        return IsNullExpression(
            reader.expect_word('isnull'),
            ArgumentsListExpression.consume(reader),
        )

class AliasedScalarIdentifierExpression(ScalarExpression):

    def __init__(self, expression: ScalarExpression, _as: TokenContext, alias: TokenContext):
        super().__init__(expression.type, [expression, _as, alias])
        self.expression = expression
        self.alias = alias
        self.has_name = True

    def get_name(self):
        return self.alias.token.value

    def trace(self, tracer):
        return self.expression.trace(tracer)
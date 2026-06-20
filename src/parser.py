import ply.yacc as yacc
from enum import Enum
from dataclasses import dataclass
from lexer import tokens, get_bar_separated_type_keywords

# Inspired from https://en.cppreference.com/c/language/operator_precedence
precedence = (
    ('right',
        'ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'MULTIPLY_ASSIGN', 'DIVIDE_ASSIGN', 'MODULO_ASSIGN',
        'BITWISE_AND_ASSIGN', 'BITWISE_OR_ASSIGN', 'BITWISE_XOR_ASSIGN',
        'L_SHIFT_ASSIGN', 'R_SHIFT_ASSIGN'),
    ('right', 'QUESTION_MARK'),
    ('left', 'LOGICAL_AND'),
    ('left', 'BITWISE_OR'),
    ('left', 'BITWISE_XOR'),
    ('left', 'BITWISE_AND'),
    ('nonassoc', 'EQUAL_EQUAL', 'NOT_EQUAL'),
    ('nonassoc', 'LESS_THAN', 'GREATER_THAN', 'LESS_EQUAL', 'GREATER_EQUAL'),
    ('left', 'BITWISE_L_SHIFT', 'BITWISE_R_SHIFT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULTIPLY', 'DIVIDE', 'MODULO'),
    ('right', 'PREFIX_PLUS_PLUS', 'PREFIX_MINUS_MINUS', 'UNARY_PLUS', 'UNARY_MINUS', 'LOGICAL_NOT', 'BITWISE_NOT', 'L_PAREN'),
    ('left', 'PLUS_PLUS', 'MINUS_MINUS', 'FUNCTION_CALL', 'L_SQUARE_BRACKET', 'DOT'),
)
# NOTE: The following are "fictious tokens" (see https://ply.readthedocs.io/en/latest/ply.html#parsing-basics)
# PREFIX_PLUS_PLUS, PREFIX_MINUS_MINUS, UNARY_PLUS, UNARY_MINUS, FUNCTION_CALL

# Expressions
# ------------------------------------------------------------------------------------------------- #

type Expr = (
    ExprBinary |
    ExprUnary |
    ExprTernary |
    ExprUnaryPostfix |
    ExprAssignment |
    ExprFieldAccess |
    ExprArraySubscript |
    ExprFunctionCall |
    ExprCast |
    ExprStringLit |
    ExprFloatLit |
    ExprIntLit |
    ExprBoolLit |
    ExprIdentifier
)

class ExprBinary:
    def __init__(self, op: str, left: Expr, right: Expr):
        self.op = op
        self.left = left
        self.right = right

class ExprUnary:
    def __init__(self, op: str, right: Expr):
        self.op = op
        self.right = right

class ExprTernary:
    def __init__(self, cond: Expr, if_true: Expr, if_false: Expr):
        self.cond = cond
        self.if_true = if_true
        self.if_false = if_false

class ExprUnaryPostfix:
    def __init__(self, op: str, right: Expr):
        self.op = op
        self.right = right

class ExprAssignment:
    def __init__(self, op: str, name: str, value: Expr):
        self.op = op
        self.name = name
        self.value = value

class ExprFieldAccess:
    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right

class ExprArraySubscript:
    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right

class ExprFunctionCall:
    def __init__(self, left: Expr, args: list[Expr]):
        self.left = left
        self.args = args

class ExprCast:
    def __init__(self, type: str, value: Expr):
        self.type = type
        self.value = value

class ExprStringLit:
    def __init__(self, value: Expr):
        self.value = value

class ExprFloatLit:
    def __init__(self, value: Expr):
        self.value = float(value)

class ExprIntLit:
    def __init__(self, value: Expr):
        if value == "NULL":
            self.value = 0
        else:
            self.value = int(value)

class ExprBoolLit:
    def __init__(self, value: Expr):
        self.value = bool(value)

class ExprIdentifier:
    def __init__(self, name: str):
        self.name = name

# Statements
# ------------------------------------------------------------------------------------------------- #

class StmtExpr:
    def __init__(self, expr: Expr):
        self.expr = expr

class StmtVarDef:
    def __init__(self, type: str, name: str, initializer: Expr|None):
        self.type = type
        self.name = name
        self.initializer = initializer

class StmtBreak:
    def __init__(self):
        pass

class StmtContinue:
    def __init__(self):
        pass

class StmtDiscard:
    def __init__(self):
        pass

# Statement parsing functions
# ------------------------------------------------------------------------------------------------- #

def p_program(p):
    'program : statement_list_opt'
    p[0] = p[1]

def p_statement_list_opt(p):
    '''statement_list_opt : empty
                          | statement_list'''
    p[0] = [] if p[1] is None else p[1]

def p_statement_list(p):
    '''statement_list : statement
                      | statement_list statement'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_statement_expr(p):
    'statement : expression SEMICOLON'
    p[0] = StmtExpr(p[1])

def p_statement_variable_declaration(p):
    '''statement : builtinType IDENTIFIER SEMICOLON
                 | IDENTIFIER IDENTIFIER SEMICOLON'''
    p[0] = StmtVarDef(p[1], p[2], None)

def p_statement_variable_definition(p):
    '''statement : builtinType IDENTIFIER ASSIGN expression SEMICOLON
                 | IDENTIFIER IDENTIFIER ASSIGN expression SEMICOLON'''
    p[0] = StmtVarDef(p[1], p[2], p[4])


def p_type_annnotation(p):
    p[0] = p[1]

p_type_annnotation.__doc__ = f'builtinType : {get_bar_separated_type_keywords()}'

# Expression parsing functions
# ------------------------------------------------------------------------------------------------- #

def p_expression_unary(p):
    '''expression : PLUS_PLUS expression %prec PREFIX_PLUS_PLUS
                  | MINUS_MINUS expression %prec PREFIX_MINUS_MINUS
                  | PLUS expression %prec UNARY_PLUS
                  | MINUS expression %prec UNARY_MINUS
                  | LOGICAL_NOT expression
                  | BITWISE_NOT expression'''
    p[0] = ExprUnary(p[1], p[2])

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression MULTIPLY expression
                  | expression DIVIDE expression
                  | expression MODULO expression
                  | expression BITWISE_AND expression
                  | expression BITWISE_XOR expression
                  | expression BITWISE_OR expression
                  | expression BITWISE_L_SHIFT expression
                  | expression BITWISE_R_SHIFT expression
                  | expression EQUAL_EQUAL expression
                  | expression NOT_EQUAL expression
                  | expression LESS_THAN expression
                  | expression GREATER_THAN expression
                  | expression LESS_EQUAL expression
                  | expression GREATER_EQUAL expression
                  | expression LOGICAL_AND expression
                  | expression LOGICAL_OR expression'''
    p[0] = ExprBinary(p[2], p[1], p[3])

def p_expression_ternary(p):
    'expression : expression QUESTION_MARK expression COLON expression'
    p[0] = ExprTernary(p[1], p[3], p[5])

def p_expression_postfix_unary(p):
    '''expression : expression PLUS_PLUS
                  | expression MINUS_MINUS'''
    p[0] = ExprUnaryPostfix(p[2], p[1])

def p_expression_assignment(p):
    '''expression : IDENTIFIER ASSIGN expression
                  | IDENTIFIER PLUS_ASSIGN expression
                  | IDENTIFIER MINUS_ASSIGN expression
                  | IDENTIFIER MULTIPLY_ASSIGN expression
                  | IDENTIFIER DIVIDE_ASSIGN expression
                  | IDENTIFIER MODULO_ASSIGN expression
                  | IDENTIFIER BITWISE_AND_ASSIGN expression
                  | IDENTIFIER BITWISE_OR_ASSIGN expression
                  | IDENTIFIER BITWISE_XOR_ASSIGN expression
                  | IDENTIFIER L_SHIFT_ASSIGN expression
                  | IDENTIFIER R_SHIFT_ASSIGN expression'''
    p[0] = ExprAssignment(p[2], p[1], p[3])

def p_expression_cast(p):
    'expression : L_PAREN builtinType R_PAREN expression'
    p[0] = ExprCast(p[2], p[4])

def p_expression_group(p):
    'expression : L_PAREN expression R_PAREN'
    p[0] = p[2]

def p_expression_function_call(p):
    'expression : expression L_PAREN argument_list_opt R_PAREN %prec FUNCTION_CALL'
    p[0] = ExprFunctionCall(p[1], p[3])

def p_argument_list_opt_empty(p):
    'argument_list_opt : empty'
    p[0] = []

def p_argument_list_opt_nonempty(p):
    'argument_list_opt : argument_list'
    p[0] = p[1]

def p_argument_list(p):
    '''argument_list : argument_list COMMA expression
                     | expression'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_expression_string_lit(p):
    'expression : STRING_LITERAL'
    p[0] = ExprStringLit(p[1])

def p_expression_float_lit(p):
    'expression : FLOAT_LITERAL'
    p[0] = ExprFloatLit(p[1])

def p_expression_int_lit(p):
    '''expression : INT_LITERAL
                  | NULL'''
    p[0] = ExprIntLit(p[1])

def p_expression_bool_lit(p):
    '''expression : TRUE
                  | FALSE'''
    p[0] = ExprBoolLit(p[1])

def p_expression_identifier(p):
    'expression : IDENTIFIER'
    p[0] = ExprIdentifier(p[1])

def p_error(p):
    print(f"ERROR at {p.lexer.source_path}:{p.lexer.lineno}: Syntax error at {p}")

def p_empty(p):
    'empty :'
    p[0] = None


parser = yacc.yacc()
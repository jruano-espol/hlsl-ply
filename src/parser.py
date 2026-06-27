import ply.yacc as yacc
from lexer import tokens, get_bar_separated_builtin_types

had_error = False

def had_parser_error() -> bool:
    global had_error
    return had_error

def parse_error(p, message):
    global had_error
    print(f"SYNTAX ERROR at {p.lexer.source_path}:{p.lexer.lineno}: {message}")
    had_error = True

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

# Utility Data Structures
# ------------------------------------------------------------------------------------------------- #

type Type = UserDefinedType | BuiltinType | TemplatedType

class UserDefinedType:
    def __init__(self, name: str):
        self.name = name

class BuiltinType:
    def __init__(self, name: str):
        self.name = name

class TemplatedType:
    def __init__(self, name: str, subtype: Type):
        self.name = name
        self.subtype = subtype

class ResourceBinding:
    def __init__(self, kind: str, number: int):
        self.kind = kind
        self.number = number

class FuncParam:
    def __init__(self, type: Type, name: str, semantic_label: str|None):
        self.type = type
        self.name = name
        self.semantic_label = semantic_label

class StructField:
    def __init__(self, type: Type, name: str, semantic_label: str|None):
        self.type = type
        self.name = name
        self.semantic_label = semantic_label

class BufferField:
    '''Used by cbuffer and tbuffer'''
    def __init__(self, type: Type, name: str):
        self.type = type
        self.name = name

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
    def __init__(self, op: str, left: Expr, right: Expr):
        self.op = op
        self.left = left
        self.right = right

class ExprFieldAccess:
    def __init__(self, left: Expr, field_name: str):
        self.left = left
        self.field_name = field_name

class ExprArraySubscript:
    def __init__(self, left: Expr, right: Expr):
        self.left = left
        self.right = right

class ExprFunctionCall:
    def __init__(self, left: Expr, args: list[Expr]):
        self.left = left
        self.args = args

class ExprCast:
    def __init__(self, type: Type, value: Expr):
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

class StmtScope:
    def __init__(self, statements):
        self.statements = statements

class StmtBreak:
    def __init__(self):
        pass

class StmtContinue:
    def __init__(self):
        pass

class StmtDiscard:
    def __init__(self):
        pass

class StmtReturn:
    def __init__(self, value: Expr|None):
        self.value = value

class StmtFuncDef:
    def __init__(self, return_type: Type, name: str, args: list[FuncParam], semantic_label: str|None, statements):
        self.return_type = return_type
        self.name = name
        self.args = args
        self.semantic_label = semantic_label
        self.statements = statements

class StmtStructDef:
    def __init__(self, name: str, fields: list[StructField]):
        self.name = name
        self.fields = fields

class StmtCbufferDef:
    def __init__(self, name: str, binding: ResourceBinding|None, fields: list[BufferField]):
        self.name = name
        self.binding = binding
        self.fields = fields

class StmtVarDef:
    def __init__(self, type: Type, name: str, binding: ResourceBinding|None, initializer: Expr|None):
        self.type = type
        self.name = name
        self.binding = binding
        self.initializer = initializer

# Statement parsing functions
# ------------------------------------------------------------------------------------------------- #

def p_program(p):
    '''program : opt_statement_list'''
    p[0] = p[1]

def p_opt_statement_list(p):
    '''opt_statement_list : empty
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
    '''statement : expression SEMICOLON'''
    p[0] = StmtExpr(p[1])

def p_statement_scope(p):
    '''statement : scope'''
    p[0] = StmtScope(p[1])

def p_statement_break(p):
    '''statement : BREAK SEMICOLON'''
    p[0] = StmtBreak()

def p_statement_continue(p):
    '''statement : CONTINUE SEMICOLON'''
    p[0] = StmtContinue()

def p_statement_discard(p):
    '''statement : DISCARD SEMICOLON'''
    p[0] = StmtDiscard()

def p_statement_return(p):
    '''statement : RETURN opt_expression SEMICOLON'''
    p[0] = StmtReturn(p[2])

def p_statement_function_definition(p):
    '''statement : any_type IDENTIFIER L_PAREN opt_parameter_list R_PAREN opt_semantic_label scope'''
    p[0] = StmtFuncDef(p[1], p[2], p[4], p[6], p[7])

def p_statement_struct_definition(p):
    '''statement : STRUCT IDENTIFIER L_CURLY_BRACE opt_struct_field_list R_CURLY_BRACE SEMICOLON'''
    p[0] = StmtStructDef(p[2], p[4])

def p_statement_cbuffer_definition(p):
    '''statement : CBUFFER IDENTIFIER opt_resource_binding L_CURLY_BRACE opt_buffer_field_list R_CURLY_BRACE'''
    p[0] = StmtCbufferDef(p[2], p[3], p[5])

def p_statement_variable_declaration(p):
    '''statement : any_type IDENTIFIER opt_resource_binding SEMICOLON'''
    p[0] = StmtVarDef(p[1], p[2], p[3], None)

def p_statement_variable_definition(p):
    '''statement : any_type IDENTIFIER opt_resource_binding ASSIGN expression SEMICOLON'''
    p[0] = StmtVarDef(p[1], p[2], p[3], p[5])

# Utility parsing functions
# ------------------------------------------------------------------------------------------------- #

def p_opt_parameter_list_empty(p):
    '''opt_parameter_list : empty'''
    p[0] = []

def p_opt_parameter_list_nonempty(p):
    '''opt_parameter_list : parameter_list'''
    p[0] = p[1]

def p_parameter_list(p):
    '''parameter_list : parameter_list COMMA parameter
                      | parameter'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_parameter(p):
    '''parameter : any_type IDENTIFIER opt_semantic_label'''
    p[0] = FuncParam(p[1], p[2], p[3])

def p_opt_struct_field_list_empty(p):
    '''opt_struct_field_list : empty'''
    p[0] = []

def p_opt_struct_field_list_nonempty(p):
    '''opt_struct_field_list : struct_field_list'''
    p[0] = p[1]

def p_struct_field_list_single(p):
    '''struct_field_list : struct_field SEMICOLON'''
    p[0] = [p[1]]

def p_struct_field_list_many(p):
    '''struct_field_list : struct_field_list struct_field SEMICOLON'''
    p[0] = p[1] + [p[2]]

def p_struct_field(p):
    '''struct_field : any_type IDENTIFIER opt_semantic_label'''
    p[0] = StructField(p[1], p[2], p[3])

def p_scope(p):
    '''scope : L_CURLY_BRACE opt_statement_list R_CURLY_BRACE'''
    p[0] = p[2]

def p_opt_buffer_field_list_empty(p):
    '''opt_buffer_field_list : empty'''
    p[0] = []

def p_opt_buffer_field_list_nonempty(p):
    '''opt_buffer_field_list : buffer_field_list'''
    p[0] = p[1]

def p_buffer_field_list_single(p):
    '''buffer_field_list : buffer_field SEMICOLON'''
    p[0] = [p[1]]

def p_buffer_field_list_many(p):
    '''buffer_field_list : buffer_field_list buffer_field SEMICOLON'''
    p[0] = p[1] + [p[2]]

def p_buffer_field(p):
    '''buffer_field : any_type IDENTIFIER'''
    p[0] = BufferField(p[1], p[2])

def p_templated_container(p):
    '''templated_container : BUFFER
                           | RWBUFFER
                           | STRUCTUREDBUFFER
                           | RWSTRUCTUREDBUFFER
                           | TEXTURE1D
                           | TEXTURE1DARRAY
                           | TEXTURE2D
                           | TEXTURE2DARRAY
                           | TEXTURE2DMS
                           | TEXTURE2DMSARRAY
                           | TEXTURE3D
                           | TEXTURECUBE
                           | TEXTURECUBEARRAY
                           | RWTEXTURE1D
                           | RWTEXTURE1DARRAY
                           | RWTEXTURE2D
                           | RWTEXTURE2DARRAY
                           | RWTEXTURE3D'''
    p[0] = p[1]

def p_builtin_type(p):
    p[0] = BuiltinType(p[1])

p_builtin_type.__doc__ = f'builtin_type : {get_bar_separated_builtin_types()}'

def p_templated_type(p):
    '''templated_type : templated_container LESS_THAN any_type GREATER_THAN'''
    p[0] = TemplatedType(p[1], p[3])

def p_user_defined_type(p):
    '''user_defined_type : IDENTIFIER'''
    p[0] = UserDefinedType(p[1])

def p_any_type(p):
    '''any_type : builtin_type
                | templated_type
                | user_defined_type'''
    p[0] = p[1]

def p_resource_binding(p):
    '''resource_binding : REGISTER L_PAREN IDENTIFIER R_PAREN'''
    register = p[3]
    register_type = register[0].lower()
    register_number = register[1:]

    VALID_TYPES = ['t', 'u', 'b', 's', 'c']
    if register_type not in VALID_TYPES:
        valid_types = ' '.join(VALID_TYPES + [x.upper() for x in VALID_TYPES])
        parse_error(p, f"Expected a valid register type (valid types: {valid_types})")

    try:
        register_number = int(register_number)
    except ValueError as e:
        parse_error(p, f"Expected a number after the register type ({e})")

    p[0] = ResourceBinding(register_type, register_number)

def p_opt_resource_binding(p):
    '''opt_resource_binding : COLON resource_binding'''
    p[0] = p[2]

def p_opt_resource_binding_empty(p):
    '''opt_resource_binding : empty'''
    p[0] = p[1]

def p_opt_semantic_label(p):
    '''opt_semantic_label : COLON IDENTIFIER'''
    p[0] = p[2]

def p_opt_semantic_label_empty(p):
    '''opt_semantic_label : empty'''
    p[0] = p[1]

def p_empty(p):
    '''empty :'''
    p[0] = None

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
    '''expression : expression QUESTION_MARK expression COLON expression'''
    p[0] = ExprTernary(p[1], p[3], p[5])

def p_expression_postfix_unary(p):
    '''expression : expression PLUS_PLUS
                  | expression MINUS_MINUS'''
    p[0] = ExprUnaryPostfix(p[2], p[1])

def p_expression_assignment(p):
    '''expression : expression ASSIGN expression
                  | expression PLUS_ASSIGN expression
                  | expression MINUS_ASSIGN expression
                  | expression MULTIPLY_ASSIGN expression
                  | expression DIVIDE_ASSIGN expression
                  | expression MODULO_ASSIGN expression
                  | expression BITWISE_AND_ASSIGN expression
                  | expression BITWISE_OR_ASSIGN expression
                  | expression BITWISE_XOR_ASSIGN expression
                  | expression L_SHIFT_ASSIGN expression
                  | expression R_SHIFT_ASSIGN expression'''
    p[0] = ExprAssignment(p[2], p[1], p[3])

def p_expression_field_access(p):
    '''expression : expression DOT IDENTIFIER'''
    p[0] = ExprFieldAccess(p[1], p[3])

def p_expression_cast(p):
    '''expression : L_PAREN builtin_type R_PAREN expression'''
    p[0] = ExprCast(p[2], p[4])

def p_expression_group(p):
    '''expression : L_PAREN expression R_PAREN'''
    p[0] = p[2]

def p_expression_function_call(p):
    '''expression : expression L_PAREN opt_argument_list R_PAREN %prec FUNCTION_CALL'''
    p[0] = ExprFunctionCall(p[1], p[3])

def p_opt_argument_list_empty(p):
    '''opt_argument_list : empty'''
    p[0] = []

def p_opt_argument_list_nonempty(p):
    '''opt_argument_list : argument_list'''
    p[0] = p[1]

def p_argument_list(p):
    '''argument_list : argument_list COMMA expression
                     | expression'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_expression_string_lit(p):
    '''expression : STRING_LITERAL'''
    p[0] = ExprStringLit(p[1])

def p_expression_float_lit(p):
    '''expression : FLOAT_LITERAL'''
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

def p_opt_expression(p):
    '''opt_expression : expression
                      | empty'''
    p[0] = p[1]

def p_error(p):
    parse_error(p, p)

parser = yacc.yacc()
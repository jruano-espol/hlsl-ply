import ply.lex as lex
from preprocessor import Preprocessor

# List of token names.
tokens = [
    'STRING_LITERAL',
    'FLOAT_LITERAL',
    'INT_LITERAL',
    'IDENTIFIER',
    'PLUS_PLUS',
    'MINUS_MINUS',
    'PLUS',
    'MINUS',
    'MULTIPLY',
    'DIVIDE',
    'MODULO',
    'LESS_THAN',
    'EQUAL_EQUAL',
    'NOT_EQUAL',
    'GREATER_THAN',
    'LESS_EQUAL',
    'GREATER_EQUAL',
    'BITWISE_NOT',
    'BITWISE_AND',
    'BITWISE_OR',
    'BITWISE_XOR',
    'BITWISE_L_SHIFT',
    'BITWISE_R_SHIFT',
    'LOGICAL_NOT',
    'LOGICAL_AND',
    'LOGICAL_OR',
    'L_PAREN',
    'R_PAREN',
    'L_SQUARE_BRACKET',
    'R_SQUARE_BRACKET',
    'L_CURLY_BRACE',
    'R_CURLY_BRACE',
    'ASSIGN',
    'PLUS_ASSIGN',
    'MINUS_ASSIGN',
    'MULTIPLY_ASSIGN',
    'DIVIDE_ASSIGN',
    'MODULO_ASSIGN',
    'BITWISE_AND_ASSIGN',
    'BITWISE_OR_ASSIGN',
    'BITWISE_XOR_ASSIGN',
    'L_SHIFT_ASSIGN',
    'R_SHIFT_ASSIGN',
    'DOT',
    'COMMA',
    'QUESTION_MARK',
    'COLON',
    'COLON_COLON',
    'SEMICOLON',
]

PRIMITIVE_TYPE_KEYWORDS = {'bool', 'int', 'uint', 'dword', 'half', 'float', 'double', 'void', 'string'}
VECTOR_TYPE_KEYWORDS = {'float2', 'float3', 'float4'}
MATRIX_TYPE_KEYWORDS = {'float4x4'}
BOOL_NULL_LITERAL_KEYWORDS = {'true', 'false', 'NULL'}
TYPE_DECLARATION_KEYWORDS = {'struct', 'typedef', 'namespace'}
VARIABLE_QUALIFIER_KEYWORDS = {'const', 'static', 'uniform'}
PARAMETER_MODIFIER_KEYWORDS = {'in', 'out', 'inout'}
CONTROL_FLOW_KEYWORDS = {'if', 'else', 'switch', 'case', 'default', 'for', 'while', 'do', 'break', 'continue', 'return', 'discard'}
REGISTER_KEYWORD = 'register'
RO_BUFFER_RESOURCE_KEYWORDS = {'Buffer', 'StructuredBuffer', 'ByteAddressBuffer', 'Texture1D', 'Texture1DArray', 'Texture2D', 'Texture2DArray', 'Texture2DMS', 'Texture2DMSArray', 'Texture3D', 'TextureCube', 'TextureCubeArray'}
WO_BUFFER_RESOURCE_KEYWORDS = {'RWBuffer', 'RWStructuredBuffer', 'RWByteAddressBuffer', 'RWTexture1D', 'RWTexture1DArray', 'RWTexture2D', 'RWTexture2DArray', 'RWTexture3D'}
SAMPLING_KEYWORDS = {'sampler', 'SamplerComparisonState', 'SamplerState'}
BUFFER_CONSTANT_KEYWORDS = {'cbuffer', 'tbuffer'}
CONVERSION_MODIFIER_KEYWORDS = {'unorm', 'snorm'}

keywords = set()
keywords.update(PRIMITIVE_TYPE_KEYWORDS)
keywords.update(VECTOR_TYPE_KEYWORDS)
keywords.update(MATRIX_TYPE_KEYWORDS)
keywords.update(BOOL_NULL_LITERAL_KEYWORDS)
keywords.update(TYPE_DECLARATION_KEYWORDS)
keywords.update(VARIABLE_QUALIFIER_KEYWORDS)
keywords.update(PARAMETER_MODIFIER_KEYWORDS)
keywords.update(CONTROL_FLOW_KEYWORDS)
keywords.add(REGISTER_KEYWORD)
keywords.update(RO_BUFFER_RESOURCE_KEYWORDS)
keywords.update(WO_BUFFER_RESOURCE_KEYWORDS)
keywords.update(SAMPLING_KEYWORDS)
keywords.update(BUFFER_CONSTANT_KEYWORDS)
keywords.update(CONVERSION_MODIFIER_KEYWORDS)
tokens.extend([x.upper() for x in keywords])

# Regular expression rules for tokens.
t_PLUS_PLUS = r'\+\+'
t_MINUS_MINUS = r'--'
t_PLUS = r'\+'
t_MINUS = r'-'
t_MULTIPLY = r'\*'
t_DIVIDE = r'/'
t_MODULO = r'%'
t_LESS_THAN = r'<'
t_EQUAL_EQUAL = r'=='
t_NOT_EQUAL = r'!='
t_GREATER_THAN = r'>'
t_LESS_EQUAL = r'<='
t_GREATER_EQUAL = r'>='
t_BITWISE_NOT = r'~'
t_BITWISE_AND = r'&'
t_BITWISE_OR = r'\|'
t_BITWISE_XOR = r'\^'
t_BITWISE_L_SHIFT = r'<<'
t_BITWISE_R_SHIFT = r'>>'
t_LOGICAL_NOT = r'!'
t_LOGICAL_AND = r'&&'
t_LOGICAL_OR = r'\|\|'
t_L_PAREN = r'\('
t_R_PAREN = r'\)'
t_L_SQUARE_BRACKET = r'\['
t_R_SQUARE_BRACKET = r'\]'
t_L_CURLY_BRACE = r'\{'
t_R_CURLY_BRACE = r'\}'
t_ASSIGN = r'='
t_PLUS_ASSIGN = r'\+='
t_MINUS_ASSIGN = r'-='
t_MULTIPLY_ASSIGN = r'\*='
t_DIVIDE_ASSIGN = r'/='
t_MODULO_ASSIGN = r'%='
t_BITWISE_AND_ASSIGN = r'&='
t_BITWISE_OR_ASSIGN = r'\|='
t_BITWISE_XOR_ASSIGN = r'\^='
t_L_SHIFT_ASSIGN = r'<<='
t_R_SHIFT_ASSIGN = r'>>='
t_DOT = r'\.'
t_COMMA = r','
t_QUESTION_MARK = r'\?'
t_COLON = r':'
t_COLON_COLON = r'::'
t_SEMICOLON = r';'

def t_IDENTIFIER(t):
    r'[A-Za-z_]\w*'
    if t.value in keywords:
        t.type = t.value.upper()
    return t

def t_newline(t):
    r'(\r?\n)+'
    t.lexer.lineno += len(t.value)

def t_SINGLE_LINE_COMMENT(t):
    r'\/\/[^\n]*\n?'
    t.lexer.lineno += t.value.count('\n')

def t_MULTI_LINE_COMMENT(t):
    r'\/\*(?:.|\n)*?\*\/'
    t.lexer.lineno += t.value.count('\n')

def t_STRING_LITERAL(t):
    r'"(\\.|[^"\\])*"'
    return t

def t_FLOAT_LITERAL(t):
    r'\d+\.\d+([eE][+-]?\d+)?'
    t.value = float(t.value)
    return t

def t_INT_LITERAL(t):
    r'(0[xX][0-9a-fA-F]+|\d+)'
    if t.value.lower().startswith('0x'):
        t.value = int(t.value, 16)
    else:
        t.value = int(t.value, 10)
    return t

def t_error(t):
    print(f"ERROR at {t.lexer.source_path}:{t.lexer.lineno}: Illegal character '{t.value[0]}'.")
    t.lexer.had_error = True
    t.lexer.skip(1)

t_ignore = ' \t\v\f'

def make_lexer(preprocessor: Preprocessor):
    lexer = lex.lex()
    lexer.source_path = preprocessor.path
    lexer.had_error = False
    lexer.input(preprocessor.get_expanded_source_code())
    return lexer

def get_bar_separated_type_keywords():
    sep = '\n | '
    result = ''
    result += sep.join([x.upper() for x in PRIMITIVE_TYPE_KEYWORDS]) + sep
    result += sep.join([x.upper() for x in VECTOR_TYPE_KEYWORDS]) + sep
    result += sep.join([x.upper() for x in MATRIX_TYPE_KEYWORDS]) + sep
    result += sep.join([x.upper() for x in RO_BUFFER_RESOURCE_KEYWORDS]) + sep
    result += sep.join([x.upper() for x in WO_BUFFER_RESOURCE_KEYWORDS]) + sep
    result += sep.join([x.upper() for x in SAMPLING_KEYWORDS])
    return result
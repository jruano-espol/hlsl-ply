import sys
import os
from preprocessor import Preprocessor
from lexer import make_lexer, had_lexer_error
from parser import parser, had_parser_error, str_from_ast

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} path/to/source_code.hlsl")
        sys.exit(1)
    file_path = sys.argv[1]
    preproc = Preprocessor(file_path)
    source_code = preproc.get_expanded_source_code()
    lexer = make_lexer(preproc.path, source_code)
    if had_lexer_error():
        pretty_print_preprocessed(source_code)
        exit(1)
    ast = parser.parse(lexer=lexer)
    if had_parser_error():
        pretty_print_preprocessed(source_code)
        exit(1)

    log_path = f'logs/log-{os.path.basename(file_path)}.txt'
    with open(log_path, 'w') as f:
        print(str_from_ast(ast), file=f)

    print("\nSUCCESS: The code has no errors.")

def pretty_print_preprocessed(source_code: str):
    print("")
    for i, line in enumerate(source_code.splitlines()):
        print(f"{i+1}: {line}")

if __name__ == "__main__":
    main()
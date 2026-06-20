import sys
from preprocessor import Preprocessor
from lexer import make_lexer
from parser import parser

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} path/to/source_code.hlsl")
        sys.exit(1)
    file_path = sys.argv[1]
    preproc = Preprocessor(file_path)
    lexer = make_lexer(preproc)
    if lexer.had_error:
        exit(1)
    ast = parser.parse(lexer=lexer)
    print(ast)

if __name__ == "__main__":
    main()
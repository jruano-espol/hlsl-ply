import sys
from preprocessor import Preprocessor
from lexer import make_lexer
from datetime import datetime


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} path/to/source_code.hlsl")
        sys.exit(1)
    file_path = sys.argv[1]
    preproc = Preprocessor(file_path)
    lexer = make_lexer(preproc)
    if lexer.had_error:
        exit(1)
    output_filename = datetime.now().strftime("lexico-AntonyRuano-%d-%m-%Y-%Hh%M.txt")
    with open(f'logs/{output_filename}', 'w') as f:
        print(f"Log generado a partir del archivo {file_path}\n", file=f)
        for token in lexer:
            print(token, file=f)


if __name__ == "__main__":
    main()
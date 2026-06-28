import re
import os

def read_entire_file(path: str) -> str:
    '''Recieves a file path and returns a string containing its contents'''
    with open(path) as file:
        return file.read()

class Preprocessor:
    '''NOTE: Only preprocesses #include'''

    def __init__(self, path: str):
        self.path = path
        self.source_code = read_entire_file(path)
        self.expanded_files = []

    def get_expanded_source_code(self) -> str:
        expansion_count = 0
        while "#include" in self.source_code:
            if expansion_count > 16:
                print("ERROR: Too many #include expansions.")
                exit(1)
            self._expand()
            expansion_count += 1
        return self.source_code
    
    def _expand(self) -> str:
        contents = ""
        for index, line in enumerate(self.source_code.splitlines()):
            if line.strip().startswith("#include"):
                matches = re.findall(r'"([^"]*)"', line)
                if len(matches) != 1:
                    print(f"ERROR at {self.source_code}:{index+1}: Expected one import path.")
                    exit(1)
                filename: str = matches[0]
                if not (filename.endswith(".hlsl") or filename.endswith(".hlsli")):
                    print(f"ERROR at {self.source_code}:{index+1}: Expected to include a hlsl or hlsli file.")
                    exit(1)
                if filename not in self.expanded_files:
                    self.expanded_files.append(filename)
                    path = os.path.join(os.path.dirname(self.path), filename)
                    subcontents = read_entire_file(path)
                    contents += subcontents
            else:
                contents += line + '\n'
        self.source_code = contents

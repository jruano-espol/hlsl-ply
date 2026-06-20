import re
import os

def read_entire_file(path: str) -> str:
    '''Recieves a file path and returns a string containing its contents'''
    with open(path) as file:
        return file.read()

class Preprocessor:
    '''NOTE: Only preprocesses #include and not recursively'''

    def __init__(self, path: str):
        self.path = path
        self.source_code = read_entire_file(path)
    
    def get_expanded_source_code(self) -> str:
        contents = []
        for index, line in enumerate(self.source_code.splitlines()):
            if line.strip().startswith("#include"):
                matches = re.findall(r'"([^"]*)"', line)
                if len(matches) != 1:
                    print(f"ERROR at {self.source_code}:{index+1}: Expected one import path.")
                    exit(1)
                path = matches[0]
                if not (path.endswith(".hlsl") or path.endswith(".hlsli")):
                    print(f"ERROR at {self.source_code}:{index+1}: Expected to include a hlsl or hlsli file.")
                    exit(1)
                path = os.path.join(os.path.dirname(self.path), path)
                subcontents = read_entire_file(path)
                contents.extend(subcontents)
            else:
                contents.extend(line)
                contents.append('\n')
        contents = ''.join(contents)
        return contents
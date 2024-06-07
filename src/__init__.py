import sys
import os
import os.path

from .parser import parse_all
from .context import Context

def main():
    in_path = 'input'
    out_path = 'output'

    if len(sys.argv) == 3:
        in_path = sys.argv[1].removesuffix(os.pathsep)
        out_path = sys.argv[2].removesuffix(os.pathsep)

    print(f'Input: {in_path}, Output: {out_path}', file=sys.stderr)

    context = Context(in_path, out_path, parse_all)
    context.process()

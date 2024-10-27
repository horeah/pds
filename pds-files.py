import sys
import pickle
import argparse
import os
from pathlib import Path
from itertools import chain

parser = argparse.ArgumentParser(prog='pds-files')
parser.add_argument('path', nargs='*', default=[Path()], type=Path)
parser.add_argument('-R', '--recursive', action='store_true')
args = parser.parse_args()

paths = iter(())
if sys.platform == 'win32':
    for path in args.path:
        if '*' in str(path) or '?' in str(path):
            if path.is_absolute():
                anchor = Path(path.anchor)
                paths = chain(paths,
                              (anchor / p for p in anchor.glob('/'.join(path.parts[1:]))))
            else:
                paths = chain(paths, (p for p in Path().glob(str(path))))
        else:
            if path.is_dir():
                paths = chain(paths, (p for p in path.glob('**/*' if args.recursive else '*')))
            else:
                paths = chain(paths, iter((path,)))
else:
    for path in args.path:
        if path.is_dir():
            paths = chain(paths, (p for p in path.glob('**/*' if args.recursive else '*')))
        else:
            paths = chain(paths, iter((path,)))


if os.isatty(sys.stdout.fileno()):
    output = print
else:
    output = lambda obj: pickle.dump(obj, sys.stdout.buffer)

for path in paths:
    output(path)

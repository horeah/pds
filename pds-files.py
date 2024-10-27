import sys
import pickle
import argparse
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

pds_code = open(Path(__file__).parent / 'pds.py').read()
for path in paths:
    sys.argv = ['pds.py', 'none', f'pathlib.Path("{path.as_posix()}")']
    exec(pds_code, globals(), {})

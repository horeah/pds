import sys
import pickle
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(prog='pds-files')
parser.add_argument('path', nargs='*', default='.')
parser.add_argument('-R', '--recursive', action='store_true')
args = parser.parse_args()

if sys.platform == 'win32':
    args.path = [g for p in args.path for g in (Path('.').glob(p) if p != '.' else p)]
                                         
for p in args.path:
    p = Path(p)
    expression = f'pathlib.Path("{p}")'
    if p.is_dir():
        pattern = '**/*' if args.recursive else '*'
        expression += f'.glob("{pattern}")'
    sys.argv = ['pds.py', 'none', expression]
    exec(open(Path(__file__).parent / 'pds.py').read(), globals(), {})

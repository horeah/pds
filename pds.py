import sys
import os
import pickle
import argparse

import pathlib

parser = argparse.ArgumentParser(prog='pds')
parser.add_argument('mode', choices=('none', 'each', 'filter', 'iter'))
parser.add_argument('expression')
args = parser.parse_args(sys.argv[1:])

def iterator():
    while True:
        try:
            x = pickle.load(sys.stdin.buffer)
            yield x
        except EOFError:
            break

it = iterator()

output = print if os.isatty(sys.stdout.fileno()) else lambda o: pickle.dump(o, sys.stdout.buffer)

match args.mode:
    case 'none':
        r = eval(args.expression, {'pathlib': pathlib})
        if hasattr(r, '__next__'):
            for e in r:
                output(e)
        else:
            output(r)
    case 'each':
        for x in it:
            y = eval(args.expression, {'pathlib': pathlib}, {'x': x})
            output(y)
    case 'filter':
        for x in it:
            f = eval(args.expression, {'pathlib': pathlib}, {'x': x})
            if f:
                output(x)
    case 'iter':
        r = eval(args.expression, {'it': it})
        if hasattr(r, '__next__'):
            for e in r:
                output(e)
        else:
            output(r)
                

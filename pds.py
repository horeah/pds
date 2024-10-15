import sys
import os
import pickle
import argparse

import pathlib

parser = argparse.ArgumentParser(prog='pds')
parser.add_argument('mode', choices=('none', 'each', 'filter', 'iter', 'list'))
parser.add_argument('expression')
parser.add_argument('--input', choices=('object', 'text'), default='object')
parser.add_argument('--output', choices=('object', 'text'), default='object')
args = parser.parse_args()

if os.isatty(sys.stdout.fileno()):
    args.output = 'text'

def read_line():
    l = sys.stdin.readline().strip()
    if not l:
        raise EOFError
    return l

match args.input:
    case 'object':
        input = lambda: pickle.load(sys.stdin.buffer)
    case 'text':
        input = read_line

match args.output:
    case 'object':
        output = lambda o: pickle.dump(o, sys.stdout.buffer)
    case 'text':
        output = print

def iterator():
    while True:
        try:
            yield input()
        except EOFError:
            break

it = iterator()

match args.mode:
    case 'none':
        r = eval(args.expression, {'pathlib': pathlib})
        if hasattr(r, '__next__'):
            for e in r:
                output(e)
        else:
            output(r)
    case 'each':
        for i, x in enumerate(it):
            y = eval(args.expression, {'pathlib': pathlib}, {'i': i, 'x': x})
            output(y)
    case 'filter':
        for i, x in enumerate(it):
            f = eval(args.expression, {'pathlib': pathlib}, {'i': i, 'x': x})
            if f:
                output(x)
    case 'iter' | 'list':
        r = eval(args.expression, {'it': it} if args.mode == 'iter' else {'l': list(it)})
        try:
            for e in r:
                output(e)
        except TypeError:
            output(r)
                

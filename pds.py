import sys
import os
import pickle

import pathlib

mode = sys.argv[1]
expr = sys.argv[2]

def iterator():
    while True:
        try:
            x = pickle.load(sys.stdin.buffer)
            yield x
        except EOFError:
            break

it = iterator()

output = print if os.isatty(sys.stdout.fileno()) else lambda o: pickle.dump(o, sys.stdout.buffer)

match mode:
    case '--none':
        r = eval(expr, {'pathlib': pathlib})
        if hasattr(r, '__next__'):
            for e in r:
                output(e)
        else:
            output(r)
    case '--each':
        for x in it:
            y = eval(expr, {'pathlib': pathlib}, {'x': x})
            output(y)
    case '--filter':
        for x in it:
            f = eval(expr, {'pathlib': pathlib}, {'x': x})
            if f:
                output(x)
    case '--iter':
        r = eval(expr, {'it': it})
        if hasattr(r, '__next__'):
            for e in r:
                output(e)
        else:
            output(r)
                

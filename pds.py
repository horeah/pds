import sys
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

match mode:
    case '--none':
        r = eval(expr, {'pathlib': pathlib})
        if hasattr(r, '__next__'):
            for e in r:
                pickle.dump(e, sys.stdout.buffer)
        else:
            pickle.dump(r, sys.stdout.buffer)
    case '--each':
        for x in it:
            y = eval(expr, {'pathlib': pathlib}, {'x': x})
            pickle.dump(y, sys.stdout.buffer)
    case '--filter':
        for x in it:
            f = eval(expr, {'pathlib': pathlib}, {'x': x})
            if f:
                pickle.dump(x, sys.stdout.buffer)
    case '--iter':
        r = eval(expr, {'it': it})
        if hasattr(r, '__next__'):
            for e in r:
                pickle.dump(e, sys.stdout.buffer)
        else:
            pickle.dump(r, sys.stdout.buffer)
                


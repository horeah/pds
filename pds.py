import sys
import os
import pickle
import argparse
import ast
import importlib


def main():
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

    def extract_modules(expr):
        class ModuleExtractor(ast.NodeVisitor):
            def __init__(self):
                self.modules = []

            def generic_visit(self, node):
                if (isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and not node.value.id in {'i', 'x', 'it', 'l'}):
                        self.modules.append(node.value.id)
                super().generic_visit(node)

        extractor = ModuleExtractor()
        extractor.visit(ast.parse(expr))
        return extractor.modules

    modules = {}
    for module in extract_modules(args.expression):
        try:
            modules[module] = importlib.import_module(module)
        except ModuleNotFoundError:
            pass

    def iterator():
        while True:
            try:
                yield input()
            except EOFError:
                break

    it = iterator()

    match args.mode:
        case 'none':
            r = eval(args.expression, modules)
            if hasattr(r, '__next__'):
                for e in r:
                    output(e)
            else:
                output(r)
        case 'each':
            for i, x in enumerate(it):
                y = eval(args.expression, modules, {'i': i, 'x': x})
                output(y)
        case 'filter':
            for i, x in enumerate(it):
                f = eval(args.expression, modules, {'i': i, 'x': x})
                if f:
                    output(x)
        case 'iter' | 'list':
            r = eval(args.expression, modules, {'it': it} if args.mode == 'iter' else {'l': list(it)})
            try:
                for e in r:
                    output(e)
            except TypeError:
                output(r)


class _DummyContext(object):
    """
    No-op context replacement (to allow pickling) for e.g. psutil.Process._lock
    """
    def __enter__(*args):
        pass

    def __exit__(*args):
        pass


if __name__ == '__main__':
    main()

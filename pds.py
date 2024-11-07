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
    parser.add_argument('-E', '--ignore-exception', action='store')
    args = parser.parse_args()

    if os.isatty(sys.stdout.fileno()):
        args.output = 'text'

    def read_line():
        l = sys.stdin.readline()
        if not l:
            raise EOFError
        return l.strip()

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

    def import_modules(expr):
        modules = {}
        for module in extract_modules(expr):
            try:
                modules[module] = importlib.import_module(module)
            except ModuleNotFoundError:
                pass
        return modules

    _EXCEPTION_IN_EXPRESSION = object()
    if args.ignore_exception:
        modules = import_modules(args.ignore_exception)
        exc_type = eval(args.ignore_exception, modules)

        def eval_expr_mark_exceptions(expr, globals, locals):
            """Eval expression and return a marker value if an exception was raised"""
            try:
                return eval(expr, globals, locals)
            except exc_type:
                return _EXCEPTION_IN_EXPRESSION

        def ignore_exception_marker(func):
            """Don't call the target function if the argument is an exception marker"""
            def wrapper(arg):
                if arg != _EXCEPTION_IN_EXPRESSION:
                    func(arg)
            return wrapper

        eval_expr = eval_expr_mark_exceptions
        output = ignore_exception_marker(output)
    else:
        eval_expr = lambda expr, globals, locals: eval(expr, globals, locals)

    _swallow_broken_pipe_message()
    
    modules = import_modules(args.expression)

    def iterator():
        while True:
            try:
                yield input()
            except EOFError:
                break

    it = iterator()

    try:
        match args.mode:
            case 'none':
                r = eval_expr(args.expression, modules, locals())
                if hasattr(r, '__iter__') and not isinstance(r, str):
                    for e in r:
                        output(e)
                else:
                    output(r)
            case 'each':
                for i, x in enumerate(it):
                    y = eval_expr(args.expression, modules, {'i': i, 'x': x})
                    output(y)
            case 'filter':
                for i, x in enumerate(it):
                    f = eval_expr(args.expression, modules, {'i': i, 'x': x})
                    if f and f != _EXCEPTION_IN_EXPRESSION:
                        output(x)
            case 'iter' | 'list':
                r = eval_expr(args.expression, modules,
                              {'it': it} if args.mode == 'iter' else {'l': list(it)})
                if hasattr(r, '__iter__') and not isinstance(r, str):
                    for e in r:
                        output(e)
                else:
                    output(r)
    except BrokenPipeError:
        # Consumer has terminated
        pass


class _DummyContext(object):
    """
    No-op context replacement (to allow pickling) for e.g. psutil.Process._lock
    """
    def __enter__(*args):
        pass

    def __exit__(*args):
        pass


def _swallow_broken_pipe_message():
    orig_stderr_write = sys.stderr.write
    def write_until_broken_pipe(str):
        if str.startswith("Exception ignored in"):
            # Consumer has terminated
            sys.stderr.write = None
        else:
            orig_stderr_write(str)
    sys.stderr.write = write_until_broken_pipe


if __name__ == '__main__':
    main()

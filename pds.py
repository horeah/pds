import sys
import os
import pickle
import argparse
import ast
import importlib
from pathlib import Path
from itertools import chain


def main():
    parser = argparse.ArgumentParser(prog='pds')
    parser.add_argument('--input', choices=('auto', 'object', 'text'), default='auto')
    parser.add_argument('--output', choices=('auto', 'object', 'text'), default='auto')
    subparsers = parser.add_subparsers(dest='mode', title='modes')

    parser_none = subparsers.add_parser('none', help='Create pds stream from expression')
    parser_none.add_argument('expression', help='Expression to evaluate')
    parser_none.add_argument('-e', '--ignore-exception', action='store')

    parser_each = subparsers.add_parser('each', help='Apply expression to each object')
    parser_each.add_argument('expression', help='Expression to apply')
    parser_each.add_argument('-e', '--ignore-exception', action='store')

    parser_filter = subparsers.add_parser('filter', help='Filter objects by expression')
    parser_filter.add_argument('expression', help='Expression to filter by')
    parser_filter.add_argument('-e', '--ignore-exception', action='store')

    parser_iter = subparsers.add_parser('iter', help='Apply expression to whole input data as iterator')
    parser_iter.add_argument('expression', help='Expression to apply')

    parser_list = subparsers.add_parser('list', help='Apply expression to whole input data as list')
    parser_list.add_argument('expression', help='Expression to apply')

    parser_from_text = subparsers.add_parser('from-text', help='Create pds stream from input text')
    parser_from_text.add_argument('-s', '--separator', help='Separator for text input', 
                                  choices=('lf', 'cr', 'crlf', 'auto'), default='auto')
    
    parser_to_text = subparsers.add_parser('to-text', help='Write pds stream as text')
    parser_to_text.add_argument('-s', '--separator', help='Separator for text output',
                                 choices=('lf', 'cr', 'crlf', 'auto'), default='auto')

    parser_files = subparsers.add_parser('files', help='Create pds stream from files')
    parser_files.add_argument('path', nargs='*', default=[Path()], type=Path)
    parser_files.add_argument('-R', '--recursive', action='store_true')

    args = parser.parse_args()
    if not hasattr(args, 'ignore_exception'):
        args.ignore_exception = False

    if args.output == 'auto':
        args.output = 'text' if os.isatty(sys.stdout.fileno()) else 'object'

    if not os.isatty(sys.stdin.fileno()) and args.input == 'auto':
        bytes = sys.stdin.buffer.peek(2)
        args.input = 'object' if bytes.startswith(b'\x80\x04') else 'text'

    if args.mode in ['from-text', 'to-text']:
        args.separator = {
            'lf': '\n',
            'cr': '\r',
            'crlf': '\r\n',
            'auto': None,
        }[args.separator]
    if args.mode == 'from-text':
        sys.stdin.reconfigure(newline=args.separator)
    if args.mode == 'to-text':
        sys.stdout.reconfigure(newline=args.separator)
        
    if args.mode == 'from-text' or args.input == 'text':
        def read_line():
            l = sys.stdin.readline()
            if not l:
                raise EOFError
            return l.strip()
        input = read_line
    else: 
        input = lambda: pickle.load(sys.stdin.buffer)

    if args.mode == 'to-text' or args.output == 'text':
        output = print
    else:
        output = lambda o: pickle.dump(o, sys.stdout.buffer)

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

    match args.mode:
        case 'none':
            pass
        case 'each' | 'filter' | 'iter' | 'list' | 'from-text' | 'to-text':
            def iterator():
                while True:
                    try:
                        yield input()
                    except EOFError:
                        break
            it = iterator()
        case 'files':
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
            it = paths

    if args.mode in ['from-text', 'to-text', 'files']:
        args.mode = 'each'
        args.expression = 'x'

    modules = import_modules(args.expression)

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

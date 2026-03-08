import sys
import os
import pickle
import ijson
import json
import argparse
import ast
import importlib
import psutil
import contextlib
import itertools
from itertools import chain
from pathlib import Path

PDS_VERSION = '0.1.1'


def add_exceptions_arguments(parser):
    parser.add_argument('-e', '--ignore-exception', 
                        help = 'ignore exceptions of type IGNORE_EXCEPTION',
                        action='store')
    parser.add_argument('-E', '--ignore-all-exceptions', 
                        help = 'ignore all exceptions',
                        action='store_const',
                        const='Exception',
                        dest='ignore_exception')
    parser.add_argument('-q', '--quiet',
                        help = 'suppress error messages',
                        action='store_true')


def main():
    parser = argparse.ArgumentParser(prog='pds')
    parser.add_argument('--input', choices=('auto', 'object', 'text', 'json'), default='auto')
    parser.add_argument('--output', choices=('auto', 'object', 'text', 'json'), default='auto')
    subparsers = parser.add_subparsers(dest='mode', title='modes')

    parser_none = subparsers.add_parser('none', help='Create pds stream from expression')
    parser_none.add_argument('expression', help='Expression to evaluate')
    add_exceptions_arguments(parser_none)

    parser_each = subparsers.add_parser('each', help='Apply expression to each object')
    parser_each.add_argument('expression', help='Expression to apply')
    add_exceptions_arguments(parser_each)

    parser_filter = subparsers.add_parser('filter', help='Filter objects by expression')
    parser_filter.add_argument('expression', help='Expression to filter by')
    add_exceptions_arguments(parser_filter)

    parser_count = subparsers.add_parser('count', help='Count objects')

    parser_iter = subparsers.add_parser('iter', help='Apply expression to whole input data as iterator')
    parser_iter.add_argument('expression', help='Expression to apply')

    parser_list = subparsers.add_parser('list', help='Apply expression to whole input data as list')
    parser_list.add_argument('expression', help='Expression to apply')

    parser_sort = subparsers.add_parser('sort', help='Sort objects using expression as key')
    parser_sort.add_argument('expression', help='Expression to use as key', nargs='?', default=None)
    parser_sort.add_argument('-r', '--reverse', action='store_true')

    parser_from_text = subparsers.add_parser('from-text', help='Create pds stream from input text')
    parser_from_text.add_argument('-s', '--separator', help='Separator for text input', 
                                  choices=('lf', 'cr', 'crlf', 'auto'), default='auto')
    
    parser_to_text = subparsers.add_parser('to-text', help='Write pds stream as text')
    parser_to_text.add_argument('-s', '--separator', help='Separator for text output',
                                 choices=('lf', 'cr', 'crlf', 'auto'), default='auto')

    parser_files = subparsers.add_parser('files', help='Create pds stream from files')
    parser_files.add_argument('path', nargs='*', type=Path)
    parser_files.add_argument('-R', '--recursive', action='store_true')

    parser_procs = subparsers.add_parser('procs', help='Create pds stream from processes')

    parser_procs.add_argument('-u', '--user', help='only processes belonging to USER', action='store')
    parser_procs.add_argument('-U', '--current-user', help='only processes belonging to the current user', 
                              action='store_const', const=psutil.Process().username(), dest='user')
    add_exceptions_arguments(parser_procs)

    parser.add_argument('--version', action='version', version=f'%(prog)s {PDS_VERSION}')

    args = parser.parse_args()
    if not hasattr(args, 'ignore_exception'):
        args.ignore_exception = False

    if args.output == 'auto':
        args.output = 'text' if os.isatty(sys.stdout.fileno()) else 'object'

    if not os.isatty(sys.stdin.fileno()) and args.input == 'auto':
        bytes = sys.stdin.buffer.peek(2)
        args.input = 'object' if bytes.startswith(pickle.dumps(None)[:2]) else 'text'

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
    elif args.input == 'json':
        json_iterator = ijson.items(sys.stdin, 'item')
        def read_json_object():
            try:
                return next(json_iterator)
            except StopIteration:
                raise EOFError
        input = read_json_object
    else: 
        input = lambda: pickle.load(sys.stdin.buffer)

    if args.mode == 'to-text' or args.output == 'text':
        output = print
    elif args.output == 'json':
        print('[', end='')
        comma = False
        def write_json_object(o):
            nonlocal comma
            sys.stdout.write(', ' if comma else '')
            json.dump(o, sys.stdout)
            comma = True
        output = write_json_object
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

    class ExceptionMarker(object):
        def __init__(self, exception):
            self.exception = exception

    if args.ignore_exception:
        modules = import_modules(args.ignore_exception)
        exc_type = eval(args.ignore_exception, modules)

        def eval_expr_mark_exceptions(expr, globals, locals):
            """Eval expression and return a marker value if an exception was raised"""
            try:
                return eval(expr, globals, locals)
            except exc_type as e:
                return ExceptionMarker(e)

        def ignore_exception_marker(func):
            """Don't call the target function if the argument is an exception marker"""
            def wrapper(arg):
                if isinstance(arg, ExceptionMarker):
                    if not args.quiet:
                        print(arg.exception, file=sys.stderr)
                else:
                    func(arg)
            return wrapper

        eval_expr = eval_expr_mark_exceptions
        output = ignore_exception_marker(output)
    else:
        eval_expr = lambda expr, globals, locals: eval(expr, globals, locals)

    _swallow_broken_pipe_message()

    def iterator():
        while True:
            try:
                yield input()
            except EOFError:
                break

    match args.mode:
        case 'none':
            pass
        case 'each' | 'filter' | 'count' | 'iter' | 'list' | 'sort' | 'from-text' | 'to-text':
            it = iterator()
        case 'files':
            if os.isatty(sys.stdin.fileno()):
                if not args.path:
                    args.path = [Path()]
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
            else:
                assert not args.path, 'Cannot use path argument and stdin at the same time'
                it = (Path(p) for p in iterator())
        case 'procs':
            def dummy_lock(proc):
                proc._lock = contextlib.nullcontext()
                return proc

            def belongs_to_user(proc, user):
                try:
                    return proc.username() == user
                except psutil.Error:
                    return False

            it = (dummy_lock(proc) for proc in psutil.process_iter()
                  if not args.user or belongs_to_user(proc, args.user))

    if args.mode in ['from-text', 'to-text', 'files', 'procs']:
        args.mode = 'each'
        args.expression = 'x'

    if args.mode == 'sort':
        args.mode = 'iter'
        if args.expression is not None:
            args.expression = f'lambda x: {args.expression}'
        args.expression = f'sorted(it, key={args.expression}, reverse={args.reverse})'

    if args.mode == 'count':
        args.mode = 'iter'
        args.expression = f'sum(1 for _ in it)'

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
                    if f and not isinstance(f, ExceptionMarker):
                        output(x)
            case 'iter' | 'list':
                if args.mode == 'iter':
                    vars = {'it': it}
                    modules.update({name: value
                                    for name, value in itertools.__dict__.items()
                                    if not name.startswith('_')})
                else:
                    vars = {'l': list(it)}
                r = eval_expr(args.expression, modules, vars)
                if hasattr(r, '__iter__') and not isinstance(r, str):
                    for e in r:
                        output(e)
                else:
                    output(r)
        if args.output == 'json':
            print(']')

    except BrokenPipeError:
        # Consumer has terminated
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

import unittest
import sys
from subprocess import Popen, PIPE
from os import linesep


def pds_text(mode, expr, lines):
    process = Popen([sys.executable, 'pds.py', mode, '--input=text', '--output=text', expr],
                    stdin=PIPE, stdout=PIPE, text=True)
    stdout, _ = process.communicate('\n'.join(lines))
    return stdout.rstrip('\n').split('\n')


input_lines = ['line1', 'line2', 'long line 3']


class TestPds(unittest.TestCase):
    """
    Integration tests based on a "text input, text output" workflow.
    """
    def test_none(self):
        self.assertEqual(pds_text('none', 'iter(range(3))', []),
                         ['0', '1', '2'])

    def test_each(self):
        self.assertEqual(pds_text('each', 'x', input_lines),
                         input_lines)
        self.assertEqual(pds_text('each', 'x.upper()', input_lines),
                         [line.upper() for line in input_lines])
        self.assertEqual(pds_text('each', 'len(x)', input_lines),
                         [str(len(line)) for line in input_lines])

    def test_filter(self):
        self.assertEqual(pds_text('filter', 'True', input_lines),
                         input_lines)
        self.assertEqual(pds_text('filter', 'x.endswith("2")', input_lines),
                         ['line2'])

    def test_iter(self):
        self.assertEqual(pds_text('iter', 'it', input_lines),
                         input_lines)
        self.assertEqual(pds_text('iter', '(x.upper() for x in it)', input_lines),
                         [line.upper() for line in input_lines])
        self.assertEqual(pds_text('iter', 'len(list(it))', input_lines),
                         ['3'])
        self.assertEqual(pds_text('iter', 'itertools.islice(it, 2)', input_lines),
                         input_lines[:2])


    def test_list(self):
        self.assertEqual(pds_text('list', 'l', input_lines),
                         input_lines)
        self.assertEqual(pds_text('list', 'len(l)', input_lines),
                         ['3'])


if __name__ == '__main__':
    unittest.main()


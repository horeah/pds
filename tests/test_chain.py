import unittest
import sys
from pathlib import Path
from subprocess import Popen, PIPE

def pds_chain(cmds):
    segs = [[f'{sys.executable}', 'pds.py', *a] for a in cmds]
    tokens = []
    for seg in segs:
        tokens += seg
        tokens.append('|')
    tokens += ['pds', 'to-text']
    cmd = ' '.join(f'"{t}"' if t != '|' else f'{t}' for t in tokens)
    process = Popen(cmd, stdout=PIPE, shell=True, text=True)
    stdout, _ = process.communicate()
    lines = stdout.split('\n')[:-1]
    return lines

    
class TestChain(unittest.TestCase):
    """
    Integration tests for pds pipelines
    """
    def test_simple(self):
        self.assertEqual(pds_chain([['none', "iter((\'abc\', \'def\'))"],
                                    ['each', 'x.upper()']]),
                         ['ABC', 'DEF'])

    def test_broken_pipe(self):
        self.assertEqual(pds_chain([['none', 'iter(range(10000))'],
                                    ['iter', 'islice(it, 4)']]),
                         ['0', '1', '2', '3'])
        
    def test_sort(self):
        self.assertEqual(pds_chain([['none', 'iter(range(100))'],
                                    ['sort']]),
                         [str(i) for i in range(100)])
        self.assertEqual(pds_chain([['none', 'iter(range(100))'],
                                    ['sort', '--reverse', 'x']]),
                         [str(i) for i in range(99, -1, -1)])

    def test_count(self):
        self.assertEqual(pds_chain([['none', 'iter(range(100))'],
                                    ['count']]),
                         ['100'])
        self.assertEqual(pds_chain([['none', 'iter(range(100))'],
                                    ['filter', 'False'],
                                    ['count']]),
                         ['0'])



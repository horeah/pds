import unittest
import sys
import itertools
from pathlib import Path
from subprocess import Popen, PIPE

def pds_chain(cmds):
    segs = [[f'{sys.executable}', 'pds.py', *a] for a in cmds]
    tokens = []
    for seg in segs[:-1]:
        tokens += seg
        tokens.append('|')
    tokens += segs[-1]
    tokens.append('--output=text')
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
                                    ['iter', 'itertools.islice(it, 4)']]),
                         ['0', '1', '2', '3'])
        


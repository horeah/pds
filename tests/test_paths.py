import unittest
import sys
import io
import pickle
from pathlib import Path
from subprocess import Popen, PIPE

def pds_files(args):
    process = Popen(f'"{sys.executable}" pds-files.py {args}', shell=True, stdout=PIPE)
    result = []
    while True:
        try:
            result.append(pickle.load(process.stdout))
        except EOFError:
            break
    process.communicate()
    return result

class TestPdsPaths(unittest.TestCase):
    """
    Integration tests for the pds-files source script
    """
    def test_paths(self):
        self.assertEqual(pds_files('tests/paths'),
                         list(Path('tests/paths').glob('*')))
        self.assertEqual(pds_files('tests/paths/*.dat'),
                         [Path('tests/paths/c.dat')])
                         
        


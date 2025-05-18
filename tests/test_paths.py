import unittest
import sys
import io
import pickle
from pathlib import Path
from subprocess import Popen, PIPE

def pds_files(*args):
    args_str = ' '.join([*args])
    process = Popen(f'"{sys.executable}" pds.py files {args_str}', shell=True, stdout=PIPE)
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
        self.assertEqual(pds_files('tests/paths/*.txt'),
                         list(Path('tests/paths').glob('*.txt')))
        self.assertEqual(pds_files('-R', 'tests'),
                         list(Path('tests').glob('**/*')))
        self.assertEqual(pds_files(str(Path().absolute())),
                         list(p.absolute() for p in Path().glob('*')))
                         
        


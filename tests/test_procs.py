import unittest
import sys
import psutil
import pickle
from subprocess import Popen, PIPE

def pds_procs(*args):
    args_str = ' '.join([*args])
    process = Popen(f'"{sys.executable}" pds.py procs {args_str}', shell=True, stdout=PIPE)
    result = []
    while True:
        try:
            result.append(pickle.load(process.stdout))
        except EOFError:
            break
    process.communicate()
    return result

class TestPdsProcs(unittest.TestCase):
    """
    Integration tests for the pds-procs source script
    """
    def test_procs(self):
        procs = pds_procs()
        self.assertTrue(psutil.Process() in procs)
        if sys.platform == 'win32':
            self.assertEqual(procs[0].pid, 0)
            self.assertEqual(procs[0].name(), 'System Idle Process')
        else:
            self.assertEqual(procs[0].pid, 1)

    def test_user_procs(self):
        procs = pds_procs('--current-user')
        self.assertTrue(psutil.Process() in procs)

    def test_system_procs(self):
        if sys.platform == 'win32':
            procs = pds_procs('--user', '"NT AUTHORITY\\SYSTEM"')
            self.assertEqual(procs[0].pid, 0)
        else:
            procs = pds_procs('--user', 'root')
            self.assertEqual(procs[0].pid, 1)


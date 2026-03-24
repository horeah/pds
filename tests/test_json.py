import json
from types import SimpleNamespace
import unittest
import sys
from subprocess import Popen, PIPE

def pds_json(mode, expr, input, opts=[]):
    process = Popen([sys.executable, 'pds.py', '--input=json', '--output=json', mode, *opts, expr],
                    stdin=PIPE, stdout=PIPE, text=True)
    stdout, _ = process.communicate(input)
    return stdout

def pds_from_json(input, opts=[]):
    process = Popen([sys.executable, 'pds.py', '--output=text', 'from-json', *opts],
                    stdin=PIPE, stdout=PIPE, text=True)
    stdout, _ = process.communicate(input)
    return stdout

def pds_to_json(input, opts=[]):
    process = Popen([sys.executable, 'pds.py', '--input=json', 'to-json', *opts],
                    stdin=PIPE, stdout=PIPE, text=True)
    stdout, _ = process.communicate(input)
    return stdout

input_objects = [
    {"file": "pds.py", "size": 124},
    {"file": "tests/test_chain.py", "size": 8}
]


class TestJson(unittest.TestCase):
    """
    Integration tests for json input/output
    """
    def test_json(self):
        self.assertEqual(pds_json('each', 'x', json.dumps(input_objects)), json.dumps(input_objects) + '\n')
        self.assertEqual(pds_json('each', 'x["size"]', json.dumps(input_objects)), '[124, 8]\n')

    def test_from_json(self):
        self.assertEqual(pds_from_json(json.dumps(input_objects)), 
                         '\n'.join(str(obj) for obj in input_objects) + '\n')
        self.assertEqual(pds_from_json(json.dumps(input_objects), opts=['--namespace']), 
                         '\n'.join(str(SimpleNamespace(**obj)) for obj in input_objects) + '\n')
        
    def test_to_json(self):
        self.assertEqual(pds_to_json(json.dumps(input_objects)), json.dumps(input_objects) + '\n')
        self.assertEqual(pds_to_json(json.dumps(input_objects), opts=['--pretty']), 
                         json.dumps(input_objects, indent='\t') + '\n')



if __name__ == '__main__':
    unittest.main()

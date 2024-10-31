import sys
import pickle
import psutil
import os
from pds import _DummyContext

if os.isatty(sys.stdout.fileno()):
    output = print
else:
    output = lambda obj: pickle.dump(obj, sys.stdout.buffer)

for proc in psutil.process_iter():
    proc._lock = _DummyContext()
    output(proc)


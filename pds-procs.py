import sys
import pickle
import psutil
import os
from pds import _DummyContext, _swallow_broken_pipe_message

if os.isatty(sys.stdout.fileno()):
    output = print
else:
    output = lambda obj: pickle.dump(obj, sys.stdout.buffer)

_swallow_broken_pipe_message()

try:
    for proc in psutil.process_iter():
        proc._lock = _DummyContext()
        output(proc)
except BrokenPipeError:
    # Consumer has terminated
    pass

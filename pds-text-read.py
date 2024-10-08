import sys
import pickle

for x in sys.stdin.readlines():
    pickle.dump(x.strip(), sys.stdout.buffer)

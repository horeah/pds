import sys
import pickle

while True:
    try:
        x = pickle.load(sys.stdin.buffer)
    except EOFError:
        break
    print(x)

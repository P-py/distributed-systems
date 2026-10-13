import sys
import time
import zmq

context = zmq.Context()

receiver = context.socket(zmq.PULL)
receiver.bind("tcp://localhost:5558")

s = receiver.recv()

tstart = time.time()

for task_nbr in range(100):
    s = receiver.recv()
    if task_nbr % 10 == 0:
        sys.stdout.write(':')
    else:
        sys.stdout.write('.')
    sys.stdout.flush()

tend = time.time()
print(f"Tempo total decorrido: {(tend - tstart) * 1000:.0f} ms")

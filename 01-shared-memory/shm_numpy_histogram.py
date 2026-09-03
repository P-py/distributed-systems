from multiprocessing import Process
from multiprocessing.shared_memory import SharedMemory
import numpy as np
import os

DATA_SIZE = 512
BINS = 16
HIST_SIZE = BINS * np.dtype(np.uint).itemsize

def do_child_work(shdt: SharedMemory, shhst: SharedMemory):
    data = np.ndarray((DATA_SIZE,), dtype = np.uint8, buffer = shdt.buf)
    hist = np.ndarray((BINS,), dtype = np.uint, buffer = shhst.buf)

    hist[:] = np.histogram(data, bins = BINS, range = (0, 255))[0]

    print(f"[pid: {os.getpid()}] | histograma calculado")

if __name__ == "__main__":
    shdt = SharedMemory(create = True, size = DATA_SIZE)
    shhst = SharedMemory(create = True, size = HIST_SIZE)

    data = np.ndarray((DATA_SIZE,), dtype = np.uint8, buffer = shdt.buf)
    hist = np.ndarray((BINS,), dtype = np.uint, buffer = shhst.buf)

    data[:] = np.random.randint(0, 256, DATA_SIZE, dtype = np.uint8)
    hist[:] = np.zeros(BINS, dtype = np.uint)

    p = Process(target = do_child_work, args = (shdt, shhst))
    p.start()
    p.join()

    print(f"[pid: {os.getpid()}] | histograma: {hist}")
    print(f"[pid: {os.getpid()}] | total de amostras: {hist.sum()}")

    del data, hist

    shdt.close()
    shdt.unlink()
    shhst.close()
    shhst.unlink()

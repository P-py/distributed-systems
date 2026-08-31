from multiprocessing import Semaphore as SemaphoreFactory
from multiprocessing.synchronize import Semaphore
from multiprocessing.shared_memory import SharedMemory
from time import time
from random import getrandbits
import os
import sys

MEM_BLOCK_NAME = "mem_block"
MEM_BLOCK_SIZE = 64

def do_child_work(semaphore: Semaphore, mode: str):
    acq: list[float] = []
    op: list[float] = []

    shm = SharedMemory(create = False, name = MEM_BLOCK_NAME, size = MEM_BLOCK_SIZE)

    for _ in range(1000): 
        initialT = time()
        semaphore.acquire()
        acq.append(time() - initialT)

        if (mode == 'r'):
            readTime = time()
            read = bytes(shm.buf)
            op.append(time() - readTime)
        elif (mode == 'w'):
            writeTime = time()
            randomValue = getrandbits(8)
            bArray = bytes([randomValue]) * MEM_BLOCK_SIZE
            shm.buf[:MEM_BLOCK_SIZE:] = bArray
            op.append(time() - writeTime)

        semaphore.release()

    avgAcq = sum(acq) / len(acq)
    avgOp = sum(op) / len(op)

    print(f"[pid: {os.getpid()}] | tempo medio de acquire: {avgAcq:.2e}s")
    print(f"[pid: {os.getpid()}] | tempo medio de operacao [{mode}]: {avgOp:.2e}s")

    shm.close()
    sys.exit(0)

if __name__ == "__main__":
    sem = SemaphoreFactory()
    shm = SharedMemory(create = True, name = MEM_BLOCK_NAME, size = MEM_BLOCK_SIZE)

    c1 = os.fork()
    if (c1 == 0):
        do_child_work(sem, 'r')
    else:
        c2 = os.fork()
        if (c2 == 0):
            do_child_work(sem, 'w')
        else:
            os.waitpid(c1, 0)
            os.waitpid(c2, 0)

    shm.close()
    shm.unlink()
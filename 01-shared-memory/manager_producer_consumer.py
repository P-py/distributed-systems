from multiprocessing import Manager, Process
from multiprocessing.managers import SharedMemoryManager
from multiprocessing.shared_memory import ShareableList
from multiprocessing.sharedctypes import Synchronized
from multiprocessing.synchronize import Event
from random import randint
import os

ITERATIONS = 10
LIST_SIZE = 3
MAX_VALUE = 999

def producer(shl: ShareableList, idx: Synchronized, dirty: Event):
    for _ in range(ITERATIONS):
        position = randint(0, LIST_SIZE - 1)
        value = randint(0, MAX_VALUE)

        shl[position] = value
        idx.value = position

        print(f"[pid: {os.getpid()}] | produzido: shl[{position}] = {value}")
        dirty.set()

        while dirty.is_set():
            dirty.wait(0.1)

def consumer(shl: ShareableList, idx: Synchronized, dirty: Event):
    for _ in range(ITERATIONS):
        dirty.wait()

        position = idx.value
        value = shl[position]

        print(f"[pid: {os.getpid()}] | consumido: shl[{position}] = {value} | lista: {list(shl)}")

        dirty.clear()

if __name__ == "__main__":
    with Manager() as manager:
        dirty = manager.Event()
        index = manager.Value('i', 0)

        with SharedMemoryManager() as shmanager:
            shl = shmanager.ShareableList([0] * LIST_SIZE)

            p = Process(target = producer, args = (shl, index, dirty))
            c = Process(target = consumer, args = (shl, index, dirty))

            c.start()
            p.start()

            p.join()
            c.join()

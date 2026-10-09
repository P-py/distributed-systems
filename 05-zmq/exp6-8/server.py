import os
import random
import time
import zmq

def main():
    c = zmq.Context()
    s = c.socket(zmq.PUB)
    s.bind("tcp://localhost:5558")
    while True:
        topic = random.randint(ord('A'), ord('D'))
        data = random.randint(-79, 135)
        m = f'{chr(topic)} {data}'.encode()
        print(m)
        s.send(m)
        time.sleep(1)

if __name__=='__main__':
    try:
        if os.name=='nt':
            with zmq.utils.win32.allow_interrupt(): main()
        else: main()
    except KeyboardInterrupt:
        None

import os
import zmq

def main():
    c = zmq.Context()
    s = c.socket(zmq.SUB)
    s.connect("tcp://localhost:5558")
    s.setsockopt(zmq.SUBSCRIBE, b'A')
    while True:
        m = s.recv()
        print(m)

if __name__=='__main__':
    try:
        if os.name=='nt':
            with zmq.utils.win32.allow_interrupt(): main()
        else: main()
    except KeyboardInterrupt:
        None

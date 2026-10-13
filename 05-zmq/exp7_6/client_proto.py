import os
import zmq

from person_pb2 import Person

def main():
    c = zmq.Context()
    s = c.socket(zmq.SUB)
    s.connect("tcp://localhost:5558")
    s.setsockopt(zmq.SUBSCRIBE, b"protob")
    while True:
        _, payload = s.recv_multipart()
        p = Person.FromString(payload)
        print(f"Nome: {p.name}\nAltura: {p.height}\nSorte:{list(p.luck_numbers)}\n\n", end="")

if __name__=='__main__':
    try:
        if os.name=='nt':
            with zmq.utils.win32.allow_interrupt(): main()
        else: main()
    except KeyboardInterrupt:
        None

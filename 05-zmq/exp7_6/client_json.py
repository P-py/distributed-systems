import json
import os
import zmq

def main():
    c = zmq.Context()
    s = c.socket(zmq.SUB)
    s.connect("tcp://localhost:5558")
    s.setsockopt(zmq.SUBSCRIBE, b"json")
    while True:
        _, payload = s.recv_multipart()
        p = json.loads(payload)
        print(f"Nome: {p['name']}\nAltura: {p['height']}\nSorte:{p['luck_numbers']}\n\n", end="")

if __name__=='__main__':
    try:
        if os.name=='nt':
            with zmq.utils.win32.allow_interrupt(): main()
        else: main()
    except KeyboardInterrupt:
        None

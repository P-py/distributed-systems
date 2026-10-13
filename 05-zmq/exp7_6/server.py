import json
import os
import time
import zmq

from person_pb2 import Person

PESSOAS = (
    {"name": "Pessoa 1", "height": 1.70, "luck_numbers": [1, 2, 3]},
    {"name": "Pessoa 2", "height": 1.71, "luck_numbers": [4, 5, 6]},
    {"name": "Pessoa 3", "height": 1.72, "luck_numbers": [7, 8, 9]},
)

def main():
    payloads = [
        (p["name"], Person(**p).SerializeToString(), json.dumps(p, ensure_ascii=False).encode())
        for p in PESSOAS
    ]
    c = zmq.Context()
    s = c.socket(zmq.PUB)
    s.bind("tcp://localhost:5558")
    print("Publicando em tcp://localhost:5558 (Ctrl-C encerra)")
    while True:
        for name, proto, js in payloads:
            s.send_multipart([b"protob", proto])
            s.send_multipart([b"json", js])
            print(f"{name}: protob {len(proto)} bytes, json {len(js)} bytes")
            time.sleep(1)

if __name__=='__main__':
    try:
        if os.name=='nt':
            with zmq.utils.win32.allow_interrupt(): main()
        else: main()
    except KeyboardInterrupt:
        None

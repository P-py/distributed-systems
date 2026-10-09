import argparse
import os
import zmq

def main(args):
    c = zmq.Context()
    s = c.socket(zmq.REQ)
    s.connect("tcp://localhost:5558")
    try:
        s.send_string("HELO")
        greeting, operations = [f.decode() for f in s.recv_multipart()]
        print(f"Servidor: {greeting}, operações: {operations}")
        if args.op not in operations.split(","):
            print(f"Operação '{args.op}' não oferecida pelo servidor")
            return
        s.send_multipart([args.op.encode(), args.a.encode(), args.b.encode()])
        print(f"{args.op}({args.a}, {args.b}) = {s.recv_string()}")
    finally:
        s.close()
        c.term()

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('op', nargs='?', default='add')
    parser.add_argument('a', nargs='?', default='2')
    parser.add_argument('b', nargs='?', default='3')
    args = parser.parse_args()
    try:
        if os.name=='nt':
            with zmq.utils.win32.allow_interrupt(): main(args)
        else: main(args)
    except KeyboardInterrupt:
        None

import argparse
import os
import zmq

class my_application():
    def __init__(self, host="tcp://localhost:5558"):
        self.host = host
        self.c = zmq.Context()
        self.s = None

    def server(self):
        self.s = self.c.socket(zmq.REP)
        self.s.bind(self.host)
        print(f"Server listening on {self.host}...")
        while True:
            r = self.s.recv()
            print(f"{len(r)}, {r}")
            self.s.send("From server with love".encode())

    def client(self):
        self.s = self.c.socket(zmq.REQ)
        self.s.connect(self.host)
        self.s.send_string("Get the tip!")
        r = self.s.recv_string()
        print(r)

    def closing(self):
        if self.s: self.s.close()
        if self.c: self.c.term()

    def __del__(self):
        self.closing()

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', action='store_true')
    args = parser.parse_args()
    app = my_application()
    def process_choice():
        if args.server:
            try: app.server()
            except KeyboardInterrupt: None
        else:
            app.client()
    if os.name=='nt':
        with zmq.utils.win32.allow_interrupt(): process_choice()
    else: process_choice()

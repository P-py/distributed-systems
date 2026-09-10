import argparse
import socket
import threading
import time

HOST = 'localhost'
PORT = 50007
DELAY = 5

def log(tag, msg):
  print(f'[{time.strftime("%H:%M:%S")}] {tag}: {msg}', flush=True)

def client(name):
  t0 = time.perf_counter()
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    log(name, f'connect() retornou em {time.perf_counter() - t0:.2f}s')
    s.sendall(b'Hello, world')
    data = s.recv(1024)
  log(name, f'Received {data!r} em {time.perf_counter() - t0:.2f}s')

def clients(n):
  ts = [threading.Thread(target=client, args=(f'client-{i + 1}',)) for i in range(n)]
  for t in ts: t.start()
  for t in ts: t.join()

def handle(conn, addr):
  with conn:
    log('server', f'Connected by {addr}')
    while True:
      data = conn.recv(1024)
      if not data: break
      time.sleep(DELAY)
      conn.sendall(data)
  log('server', f'Closed {addr}')

def server(backlog, threaded):
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(backlog)
    log('server', f'listen({backlog}), threaded={threaded}, delay={DELAY}s')
    while True:
      conn, addr = s.accept()
      if threaded:
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
      else:
        handle(conn, addr)

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--server', action='store_true')
parser.add_argument('-b', '--backlog', type=int, default=1, help='argumento do listen()')
parser.add_argument('-1', '--serial', action='store_true', help='servidor sem threads')
parser.add_argument('-n', '--clients', type=int, default=1, help='requisições simultâneas')
args = parser.parse_args()
if args.server: server(args.backlog, not args.serial)
else: clients(args.clients)

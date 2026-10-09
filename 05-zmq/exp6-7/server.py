import operator
import os
import zmq

OPERATIONS = {"add": operator.add, "subtract": operator.sub}

def calculate(op, a, b):
    if op not in OPERATIONS:
        return f"ERRO: operação desconhecida '{op}'"
    try:
        return f"{OPERATIONS[op](float(a), float(b)):g}"
    except ValueError:
        return f"ERRO: valores inválidos '{a}', '{b}'"

def main():
    c = zmq.Context()
    s = c.socket(zmq.REP)
    s.bind("tcp://localhost:5558")
    print("Servidor aguardando em tcp://localhost:5558...")
    try:
        while True:
            frames = [f.decode() for f in s.recv_multipart()]
            print(f"Recebido: {frames}")
            if frames == ["HELO"]:
                s.send_multipart([b"OLEH", ",".join(OPERATIONS).encode()])
            elif len(frames) == 3:
                s.send_string(calculate(*frames))
            else:
                s.send_string("ERRO: mensagem fora do protocolo")
    finally:
        s.close()
        c.term()

if __name__=='__main__':
    try:
        if os.name=='nt':
            with zmq.utils.win32.allow_interrupt(): main()
        else: main()
    except KeyboardInterrupt:
        None

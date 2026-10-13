from datetime import date

import zmq
import zmq.utils.win32

API_URL = "https://api.locadora-b.example/v1/aluguel"

CARROS = [
    {"id": 1, "nome": "2023/Hyundai/HB20", "valor": 139.90, "alugado": None, "tempo": 0},
    {"id": 2, "nome": "2022/Renault/Kwid", "valor": 99.90, "alugado": date(2026, 10, 12), "tempo": 3},
    {"id": 3, "nome": "2024/Jeep/Renegade", "valor": 219.90, "alugado": date(2026, 10, 11), "tempo": 7},
    {"id": 4, "nome": "2023/Honda/City", "valor": 189.90, "alugado": None, "tempo": 0},
    {"id": 5, "nome": "2021/Ford/Ka", "valor": 109.90, "alugado": None, "tempo": 0},
]


class Main():
    _pub = "tcp://localhost:5560"
    _rep = "tcp://localhost:5561"

    def __init__(self, context=None):
        self.c = context or zmq.Context.instance()
        self.sub = self.c.socket(zmq.SUB)
        self.req = self.c.socket(zmq.REQ)

    def run(self):
        with self.sub as sub, self.req as req:
            sub.connect(Main._pub)
            sub.setsockopt(zmq.SUBSCRIBE, b"QTY")
            req.connect(Main._rep)
            print(f"Locadora aguardando QTY em {Main._pub}...")
            if sub.recv_string() != "QTY":
                return
            livres = [(c["nome"], c["valor"]) for c in CARROS if c["alugado"] is None]
            req.send_string(API_URL, zmq.SNDMORE)
            req.send_pyobj((len(livres), livres))
            print(f"Enviados {len(livres)} carro(s) disponível(is) para {Main._rep}")
            print(f"Resposta do agregador: {req.recv_string()}")


def w32hk():
    zmq.Context.instance().term()


if __name__ == '__main__':
    try:
        with zmq.utils.win32.allow_interrupt(w32hk):
            Main().run()
    except KeyboardInterrupt:
        print("Fim.")

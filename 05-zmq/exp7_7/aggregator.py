import zmq
import zmq.utils.win32

LOCADORAS = 2
TENTATIVAS = 10


class Main():
    _pub = "tcp://localhost:5560"
    _rep = "tcp://localhost:5561"

    def __init__(self, context=None):
        self.c = context or zmq.Context.instance()
        self.pub = self.c.socket(zmq.PUB)
        self.rep = self.c.socket(zmq.REP)

    def run(self):
        with self.pub as pub, self.rep as rep:
            pub.bind(Main._pub)
            rep.bind(Main._rep)
            respostas = 0
            for _ in range(TENTATIVAS):
                if respostas == LOCADORAS:
                    break
                pub.send_string("QTY")
                while respostas < LOCADORAS and rep.poll(1000):
                    url = rep.recv_string()
                    qty, carros = rep.recv_pyobj()
                    rep.send_string("ACK")
                    respostas += 1
                    print(f"{url}: {qty} carro(s) disponível(is)")
                    for nome, valor in carros:
                        print(f"  {nome} - R$ {valor:.2f}/dia")
            print(f"{respostas} de {LOCADORAS} locadora(s) responderam")


def w32hk():
    zmq.Context.instance().term()


if __name__ == '__main__':
    try:
        with zmq.utils.win32.allow_interrupt(w32hk):
            Main().run()
    except KeyboardInterrupt:
        print("Fim.")

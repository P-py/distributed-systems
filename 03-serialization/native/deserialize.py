from __future__ import annotations  # list[int] em anotações no Python 3.8

from base64 import b64decode, b64encode
from dataclasses import dataclass, field
import pickle
import sys

# A classe é redefinida aqui, e não importada do serialize.py, de propósito: o
# pickle grava o módulo em que a classe foi definida (aqui, __main__) e o
# resolve no momento da leitura. Importá-la de um módulo mudaria esse caminho
# para serialize.Person e a re-serialização deixaria de bater.
@dataclass
class Person:
    Name: str
    EnrollNumber: int
    Height: float
    LuckNumbers: list[int] = field(default_factory=list)


# Stream de amostra, gerado pelo serialize.py com os dados de exemplo.
BASE64 = "gASVcgAAAAAAAACMCF9fbWFpbl9flIwGUGVyc29ulJOUKYGUfZQojAROYW1llIwLQWxhbiBUdXJpbmeUjAxFbnJvbGxOdW1iZXKUSjJ5BgCMBkhlaWdodJRHP/xR64UeuFKMC0x1Y2tOdW1iZXJzlF2UKEsHSxdLL2V1Yi4="


def main() -> None:
    if len(sys.argv) > 2:
        sys.exit("uso: python3 deserialize.py [base64]")

    encoded = sys.argv[1] if len(sys.argv) == 2 else BASE64

    try:
        decoded = b64decode(encoded, validate=True)
    except Exception as ex:
        sys.exit(f"Base64 inválido: {ex}")

    try:
        # pickle.loads importa a classe gravada no stream, e portanto executa
        # código: só rode com streams que você mesmo gerou.
        p = pickle.loads(decoded)
    except Exception as ex:
        sys.exit(f"Falha ao desserializar: {type(ex).__name__}: {ex}")

    print(f"Name: {p.Name}")
    print(f"EnrollNumber: {p.EnrollNumber}")
    print(f"Height: {p.Height}")
    print(f"LuckNumbers: {p.LuckNumbers}")

    # O @dataclass já geraria __eq__, mas a comparação por re-serialização é a
    # mesma usada do lado Java e não duplica os valores nos dois arquivos.
    if b64encode(pickle.dumps(p)).decode() == encoded:
        print("OK: objeto recuperado integralmente (re-serialização idêntica)")
    else:
        sys.exit("ATENÇÃO: a re-serialização não bate com a entrada")


if __name__ == "__main__":
    main()

from base64 import b64decode, b64encode
import sys

from google.protobuf.message import DecodeError

from MyApp_pb2 import Person


def encode(p: Person) -> str:
    return b64encode(p.SerializeToString()).decode()


def enviar() -> None:
    # Dados de amostra: o base64 não é criptografia, quem tiver a string lê
    # todos os campos em claro.
    p = Person()
    p.name = "Alan Turing"
    p.enroll_number = 424242
    p.height = 1.77
    p.luck_numbers.extend([7, 23, 47])
    print(encode(p))


def receber(encoded: str) -> None:
    try:
        decoded = b64decode(encoded, validate=True)
    except ValueError as ex:
        sys.exit(f"Base64 inválido: {ex}")

    p = Person()
    try:
        p.ParseFromString(decoded)
    except DecodeError as ex:
        sys.exit(f"Falha ao desserializar: {ex}")

    print(f"Name: {p.name}")
    print(f"EnrollNumber: {p.enroll_number}")
    print(f"Height: {p.height:.2f}")
    print(f"LuckNumbers: {list(p.luck_numbers)}")

    if encode(p) == encoded:
        print("OK: objeto recuperado integralmente (re-serialização idêntica)")
    else:
        sys.exit("ATENÇÃO: a re-serialização não bate com a entrada")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit("uso: python3 MyApp.py [base64]")

    if len(sys.argv) == 2:
        receber(sys.argv[1])
    else:
        enviar()

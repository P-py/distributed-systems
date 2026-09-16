from __future__ import annotations  # list[int] em anotações no Python 3.8

from dataclasses import asdict, dataclass, field
import json
import sys

CAMPOS = ("Name", "EnrollNumber", "Height", "LuckNumbers")


@dataclass
class Person:
    Name: str
    EnrollNumber: int
    Height: float
    LuckNumbers: list[int] = field(default_factory=list)


def enviar():
    p = Person(
        Name="Grace Hopper",
        EnrollNumber=200002,
        Height=1.60,
        LuckNumbers=[5, 13, 41],
    )
    print(json.dumps(asdict(p), separators=(",", ":"), ensure_ascii=False))


def receber(texto):
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as ex:
        sys.exit(f"JSON inválido: {ex}")

    if not isinstance(dados, dict):
        sys.exit(f"JSON inválido: esperava um objeto, veio {type(dados).__name__}")

    faltando = [c for c in CAMPOS if c not in dados]
    if faltando:
        sys.exit(f"JSON incompleto: falta(m) a(s) chave(s) {', '.join(faltando)}")

    p = Person(**{c: dados[c] for c in CAMPOS})
    print(f"Name: {p.Name}")
    print(f"EnrollNumber: {p.EnrollNumber}")
    print(f"Height: {p.Height}")
    print(f"LuckNumbers: {p.LuckNumbers}")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit("uso: python3 MyApp.py [json]")

    if len(sys.argv) == 2:
        receber(sys.argv[1])
    else:
        enviar()

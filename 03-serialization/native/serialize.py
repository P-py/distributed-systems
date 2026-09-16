from __future__ import annotations  # list[int] em anotações no Python 3.8

from base64 import b64encode
from dataclasses import dataclass, field
import pickle


@dataclass
class Person:
    Name: str
    EnrollNumber: int
    Height: float
    LuckNumbers: list[int] = field(default_factory=list)


def encode(p: Person) -> str:
    """Usado também pelo deserialize.py, para validar a volta re-serializando."""
    return b64encode(pickle.dumps(p)).decode()


if __name__ == "__main__":
    # Dados de amostra: o base64 não é criptografia, quem tiver a string lê
    # todos os campos em claro.
    p = Person(
        Name="Alan Turing",
        EnrollNumber=424242,
        Height=1.77,
        LuckNumbers=[7, 23, 47],
    )
    print(encode(p))

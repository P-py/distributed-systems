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


if __name__ == "__main__":
    # Dados de amostra
    p = Person(
        Name="Alan Turing",
        EnrollNumber=424242,
        Height=1.77,
        LuckNumbers=[7, 23, 47],
    )
    dumped = pickle.dumps(p)
    encoded = b64encode(dumped).decode()
    print(encoded)

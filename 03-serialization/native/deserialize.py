from __future__ import annotations

from base64 import b64decode
from dataclasses import dataclass, field
import pickle

@dataclass
class Person:
    Name: str
    EnrollNumber: int
    Height: float
    LuckNumbers: list[int] = field(default_factory=list)

if __name__ == "__main__":
    # Stream de amostra
    decoded = b64decode(b'gASVcgAAAAAAAACMCF9fbWFpbl9flIwGUGVyc29ulJOUKYGUfZQojAROYW1llIwLQWxhbiBUdXJpbmeUjAxFbnJvbGxOdW1iZXKUSjJ5BgCMBkhlaWdodJRHP/xR64UeuFKMC0x1Y2tOdW1iZXJzlF2UKEsHSxdLL2V1Yi4=')
    p = pickle.loads(decoded)
    print(f'Name: {p.Name}')
    print(f'EnrollNumber: {p.EnrollNumber}')
    print(f'Height: {p.Height}')
    print(f'LuckNumbers: {p.LuckNumbers}')
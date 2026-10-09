import sys

import grpc

import contact_book_pb2
import contact_book_pb2_grpc

ENDERECO = "localhost:50051"
TIMEOUT = 5

CONTATOS = (
    contact_book_pb2.Person(Name="Alan Turing", EnrollNumber=424242, Height=1.77, LuckNumbers=[7, 23, 47]),
    contact_book_pb2.Person(Name="Ada Lovelace", EnrollNumber=100001, Height=1.68, LuckNumbers=[2, 11, 29]),
    contact_book_pb2.Person(Name="Grace Hopper", EnrollNumber=200002, Height=1.60, LuckNumbers=[5, 13, 41]),
)


def imprimir(p) -> None:
    print(f"Name: {p.Name}")
    print(f"EnrollNumber: {p.EnrollNumber}")
    print(f"Height: {p.Height:.2f}")
    print(f"LuckNumbers: {list(p.LuckNumbers)}")


def executar(stub) -> None:
    print("=== 1/5: criando os 3 contatos ===")
    ids = [stub.CreateContact(p).Id for p in CONTATOS]
    print(f"ids recebidos: {ids}")

    print("\n=== 2/5: buscando o segundo contato ===")
    segundo = stub.RetrieveContact(contact_book_pb2.ContactId(Id=ids[1]))

    print("\n=== 3/5: dados do segundo contato ===")
    imprimir(segundo)
    if segundo != CONTATOS[1]:
        sys.exit("ATENÇÃO: o contato recebido não é igual ao enviado")
    print("OK: igual ao contato enviado")

    print("\n=== 4/5: removendo o primeiro contato ===")
    resposta = stub.DeleteContact(contact_book_pb2.ContactId(Id=ids[0]))
    print(f"Result: {resposta.Result}")

    print("\n=== 5/5: buscando o contato removido ===")
    try:
        stub.RetrieveContact(contact_book_pb2.ContactId(Id=ids[0]))
    except grpc.RpcError as ex:
        print(f"{ex.code().name}: {ex.details()}")
    else:
        sys.exit("ATENÇÃO: o contato removido ainda foi encontrado")


def client() -> None:
    with grpc.insecure_channel(ENDERECO) as channel:
        try:
            grpc.channel_ready_future(channel).result(timeout=TIMEOUT)
        except grpc.FutureTimeoutError:
            sys.exit(f"Servidor não respondeu em {ENDERECO} ({TIMEOUT}s): rode o server.py primeiro")

        stub = contact_book_pb2_grpc.ContactsManagerStub(channel)
        try:
            executar(stub)
        except grpc.RpcError as ex:
            sys.exit(f"Falha na chamada: {ex.code().name}: {ex.details()}")


if __name__ == "__main__":
    client()

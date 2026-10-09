from concurrent import futures
import sys
import threading

import grpc

import contact_book_pb2
import contact_book_pb2_grpc

ENDERECO = "localhost:50051"


class ContactsManagerServicer(contact_book_pb2_grpc.ContactsManagerServicer):
    def __init__(self) -> None:
        self._contatos = {}
        self._proximo_id = 1
        self._lock = threading.Lock()

    def CreateContact(self, request, context):
        with self._lock:
            contact_id = self._proximo_id
            self._proximo_id += 1
            self._contatos[contact_id] = request
        print(f"CreateContact: id={contact_id} Name={request.Name}")
        return contact_book_pb2.ContactId(Id=contact_id)

    def RetrieveContact(self, request, context):
        with self._lock:
            p = self._contatos.get(request.Id)
        if p is None:
            print(f"RetrieveContact: id={request.Id} não existe")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"contato {request.Id} não existe")
            return contact_book_pb2.Person()
        print(f"RetrieveContact: id={request.Id} Name={p.Name}")
        return p

    def DeleteContact(self, request, context):
        with self._lock:
            p = self._contatos.pop(request.Id, None)
        if p is None:
            print(f"DeleteContact: id={request.Id} não existe")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"contato {request.Id} não existe")
            return contact_book_pb2.DeleteContactResponse()
        print(f"DeleteContact: id={request.Id} removido")
        return contact_book_pb2.DeleteContactResponse(Result=f"contato {request.Id} removido")


def do_serve() -> None:
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[("grpc.so_reuseport", 0)],
    )
    contact_book_pb2_grpc.add_ContactsManagerServicer_to_server(ContactsManagerServicer(), server)
    try:
        server.add_insecure_port(ENDERECO)
    except RuntimeError:
        sys.exit(f"Não foi possível ouvir em {ENDERECO}: a porta já está em uso")
    server.start()
    print(f"Servidor ouvindo em {ENDERECO} (Ctrl+C encerra)")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Encerrando...")
        server.stop(grace=None)


if __name__ == "__main__":
    do_serve()

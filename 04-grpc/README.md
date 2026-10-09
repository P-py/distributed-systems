# 04 — gRPC

Este módulo trata de **chamada de procedimento remoto** com o **gRPC**: o
cliente chama `stub.CreateContact(p)` e o que acontece em volta — serializar,
mandar pela rede, achar o método do outro lado, devolver a resposta — é código
**gerado a partir de uma IDL**, não código escrito à mão.

## Contexto

O XML-RPC do [módulo 02](../02-sockets/README.md) já era RPC, e a ideia é a
mesma: esconder a rede atrás de uma chamada de função. O gRPC junta três peças
que estavam espalhadas pelos módulos anteriores:

| Peça | De onde vem |
|---|---|
| **Contrato + código gerado** | a IDL do [módulo 03](../03-serialization/README.md), agora descrevendo também o *serviço* |
| **Formato dos dados** | o Protocol Buffers, binário e neutro |
| **Transporte** | HTTP/2 — uma conexão multiplexada, não uma por chamada |

O `.proto` deixa de descrever só a mensagem e passa a descrever o **serviço**:
cada `rpc` nomeia a mensagem que vai e a que volta, e o `protoc` gera as duas
pontas (o *stub* do cliente e a classe base do servidor).

```proto
service ContactsManager {
  rpc CreateContact (Person) returns (ContactId) {}
  rpc RetrieveContact (ContactId) returns (Person) {}
  rpc DeleteContact (ContactId) returns (DeleteContactResponse) {}
}
```

## Estrutura

```
04-grpc/
├── contact_book.proto        # O serviço ContactsManager e as 3 mensagens
├── generate.sh / .bat        # protoc do grpcio-tools: mensagens + stubs
├── run.sh / run.bat          # Sobe o servidor, roda o cliente, mostra o log
├── server.py                 # ContactsManagerServicer: o CRUD em memória
├── client.py                 # O roteiro de 5 passos contra o servidor
├── contact_book_pb2.py       # Gerado: as mensagens
└── contact_book_pb2_grpc.py  # Gerado: o stub e a classe base do servicer
```

O `Person` é o mesmo dos outros módulos — `Name`, `EnrollNumber`, `Height`,
`LuckNumbers` — e as outras duas mensagens existem porque **toda rpc do gRPC
recebe e devolve uma mensagem**: não há como retornar um `int` pelado, daí o
`ContactId`, nem uma string pelada, daí o `DeleteContactResponse`.

> **Dados de amostra.** Os três contatos do `client.py` são nomes de exemplo
> (`Alan Turing`, `Ada Lovelace`, `Grace Hopper`); dado real nenhum é
> versionado.

## Como executar

O módulo tem o seu próprio `.venv` (gitignored) com `grpcio` e `grpcio-tools`:

```bash
cd 04-grpc
python3 -m venv .venv
.venv/bin/pip install grpcio grpcio-tools
./generate.sh                 # gera contact_book_pb2.py e _pb2_grpc.py
```

O servidor fica em primeiro plano, então o cliente vai num segundo terminal:

```bash
.venv/bin/python server.py    # terminal 1
.venv/bin/python client.py    # terminal 2
```

Ou tudo de uma vez — o `run.sh` sobe o servidor em segundo plano, roda o
cliente e imprime o log do servidor no fim:

```bash
./run.sh
```

```
=== 1/5: criando os 3 contatos ===
ids recebidos: [1, 2, 3]

=== 2/5: buscando o segundo contato ===

=== 3/5: dados do segundo contato ===
Name: Ada Lovelace
EnrollNumber: 100001
Height: 1.68
LuckNumbers: [2, 11, 29]
OK: igual ao contato enviado

=== 4/5: removendo o primeiro contato ===
Result: contato 1 removido

=== 5/5: buscando o contato removido ===
NOT_FOUND: contato 1 não existe

=== log do servidor ===
Servidor ouvindo em localhost:50051 (Ctrl+C encerra)
CreateContact: id=1 Name=Alan Turing
CreateContact: id=2 Name=Ada Lovelace
CreateContact: id=3 Name=Grace Hopper
RetrieveContact: id=2 Name=Ada Lovelace
DeleteContact: id=1 removido
RetrieveContact: id=1 não existe
```

**A porta é a 50051**, a convencional do gRPC — não a 50007 do módulo 02, então
os dois podem rodar ao mesmo tempo.

## Observações

### O erro não é exceção: é status

A rpc do passo 5 pede um contato que não existe mais. Como o `RetrieveContact`
devolve `Person`, a tentação é devolver um `Person()` vazio — e aí está a
armadilha, porque **no proto3 a mensagem em branco é um valor válido** (o mesmo
ponto medido no [módulo 03](../03-serialization/README.md#o-que-o-protocol-buffers-acrescenta):
um `Person` vazio serializa em 0 bytes e volta a ser um `Person` legítimo). O
cliente receberia `status = OK` e um contato de campos zerados, sem jeito de
distinguir "não existe" de "existe e está vazio".

O canal para dizer "deu errado" é o `context`, e ele viaja nos *trailers* do
HTTP/2, fora da mensagem:

```python
context.set_code(grpc.StatusCode.NOT_FOUND)
context.set_details(f"contato {request.Id} não existe")
```

Do lado do cliente isso chega como `grpc.RpcError`, com o código e o texto
separados — e é por isso que o `try/except` do passo 5 tem um `else` que falha:
se a chamada **não** levantar erro, o servidor deixou passar algo que devia ter
recusado.

```python
try:
    stub.RetrieveContact(contact_book_pb2.ContactId(Id=ids[0]))
except grpc.RpcError as ex:
    print(f"{ex.code().name}: {ex.details()}")   # NOT_FOUND: contato 1 não existe
else:
    sys.exit("ATENÇÃO: o contato removido ainda foi encontrado")
```

Uma exceção que escape do *servicer* também vira status, mas `UNKNOWN` com a
mensagem do Python dentro — informação de depuração vazando para o cliente:

```
CODE: UNKNOWN
DETAILS: Exception calling application: banco de dados sumiu
```

Nomear o status é o que transforma o erro em parte do contrato. (Um método que
o *servicer* não sobrescreve é o caso simpático: a classe base gerada responde
`UNIMPLEMENTED: Method not implemented!` em vez de deixar a chamada travar.)

As outras quatro rpc **não** esperam erro, e por isso o roteiro inteiro roda
dentro de um `except grpc.RpcError` que relata código e detalhes numa linha
(`Falha na chamada: UNAVAILABLE: ...`) em vez de estourar um *traceback* no meio
da saída.

### O servidor é concorrente desde a primeira linha

`grpc.server(futures.ThreadPoolExecutor(max_workers=10))` não é detalhe de
configuração: significa que **até 10 chamadas rodam ao mesmo tempo**, em threads
diferentes, sobre o mesmo objeto *servicer*. O dicionário de contatos e o
contador de ids são estado compartilhado, e `self._proximo_id += 1` não é
atômico — duas chamadas simultâneas podem ler o mesmo valor e devolver o mesmo
`Id`. Daí o `threading.Lock` em volta das três operações.

É o contraste com o `SimpleXMLRPCServer` do módulo 02, que atende uma requisição
por vez e por isso não cobrava nada disso de quem escrevia o serviço — a
condição de corrida do [módulo 01](../01-shared-memory/README.md) reaparece aqui
sem SHM nenhuma, só porque o *framework* é concorrente por padrão.

### Uma conexão, não uma por chamada

Medindo o tráfego da sessão inteira do `client.py` (as 6 chamadas) com um relé
TCP que conta conexões e bytes, contra um XML-RPC equivalente com os mesmos
dados e as mesmas operações:

| | Conexões TCP | Bytes no fio (6 chamadas) |
|---|---|---|
| gRPC | **1** | **1.516** |
| XML-RPC | 6 | 5.203 |

O XML-RPC do `xmlrpc.server` responde em HTTP/1.0: cada chamada abre e fecha a
sua conexão. O gRPC multiplexa tudo numa conexão HTTP/2, e o `Person` de 27
bytes (o mesmo payload medido no módulo 03) atravessa contra os 568 bytes do
`<methodCall>` em XML.

### 21x menos bytes não são 21x menos tempo

Mesma máquina, *loopback*, 3.000 chamadas de `CreateContact` em sequência, com
os dois servidores fazendo só a inserção num dicionário:

| | Por chamada |
|---|---|
| gRPC | 2,2 – 2,5 ms |
| XML-RPC | 3,2 – 3,5 ms |

São ~1,4x, não os 21x da diferença de payload. Em *loopback* o custo é o
ida-e-volta e o trabalho do Python em cada ponta, não os bytes: o payload só
começa a dominar quando a rede é real ou os dados são grandes — o mesmo "depende
do dado" medido no fim do módulo 03. O que o gRPC entrega aqui não é
principalmente velocidade, é o contrato gerado e o erro tipado.

### Detalhes que custam tempo

**`returns`, não `return`** — e o nome da mensagem de resposta tem de existir. O
enunciado trazia `rpc DeleteContact (ContactId) return (DeletePersonResponse)`:
dois erros numa linha, porque a palavra-chave é `returns` e a mensagem declarada
é `DeleteContactResponse`.

**A função de registro tem `Servicer` no nome.** O `protoc` gera
`add_ContactsManagerServicer_to_server`, não `add_ContactsManager_to_server`.

**O código gerado importa o outro código gerado pelo nome do módulo.** O
`contact_book_pb2_grpc.py` faz `import contact_book_pb2`, sem pacote e sem ponto
— então os dois arquivos precisam estar no mesmo diretório, e é por isso que o
`generate.sh` usa `-I.` com `--python_out=.` e `--grpc_python_out=.` na raiz do
módulo. Gerar para dentro de um pacote quebra esse import.

**Duas instâncias do servidor convivem na mesma porta, em silêncio.** O gRPC
liga o `SO_REUSEPORT` por padrão: subir o `server.py` com outro já rodando não
dá erro nenhum — o segundo *bind* é aceito e o *kernel* passa a dividir as
conexões entre os dois processos. O sintoma é o cliente conversando com o
servidor antigo (aqui apareceu como `ids recebidos: [4, 5, 6]`, de um estado que
não era o do servidor recém-subido), e `ss -ltn` mostrando duas linhas na mesma
porta. Daí as duas linhas no `do_serve()`:

```python
server = grpc.server(
    futures.ThreadPoolExecutor(max_workers=10),
    options=[("grpc.so_reuseport", 0)],
)
```

Com o `so_reuseport` desligado, o `add_insecure_port` levanta `RuntimeError` —
que o servidor transforma em uma linha (`Não foi possível ouvir em
localhost:50051: a porta já está em uso`) em vez de um *traceback*. É o
`EADDRINUSE` do [módulo 02](../02-sockets/README.md), que ali aparecia sozinho e
aqui precisa ser pedido.

**O `Height` é impresso com duas casas de propósito.** O campo é `float` de 32
bits na IDL, então o `1.77` escrito no cliente chega de volta como
`1.7699999809265137` — o mesmo detalhe medido no
[módulo 03](../03-serialization/README.md#o-que-quebra-na-volta). A conferência
do passo 3 não depende da formatação: `segundo != CONTATOS[1]` compara as duas
mensagens campo a campo, e as duas já passaram pela mesma truncagem para 32
bits.

**Esperar o servidor sem dormir um tempo fixo.** O cliente não chuta um
`sleep`: `grpc.channel_ready_future(channel).result(timeout=5)` espera o canal
ficar pronto e, se o servidor não subiu, diz isso em uma linha em vez de estourar
um `UNAVAILABLE` no meio do roteiro.

**Este módulo tem o seu próprio venv por incompatibilidade de versão.** O
`grpcio-tools` traz o runtime `protobuf` 5.x; o `03-serialization` está preso em
`protobuf==3.20.3`, porque o código gerado lá saiu do `protoc` 3.6.1 e o
runtime 4.x em diante recusa aquele formato de descritor. Os dois venvs são a
forma de os dois módulos coexistirem.

**Os nomes dos campos vêm do enunciado, em `UpperCamelCase`.** O guia de estilo
do proto pede `snake_case` (como no `MyApp.proto` do módulo 03) e deixa cada
gerador aplicar a convenção da sua linguagem. Aqui, como a aplicação é inteira
em Python, o efeito colateral é bem-vindo: os atributos ficam `p.Name`,
`p.EnrollNumber`, iguais aos nomes usados no lado Python do módulo 03.

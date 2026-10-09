# 05 — Mensageria com ZeroMQ

Este módulo trata de **mensageria embutida** com o **ZeroMQ** (0MQ): uma
biblioteca que se liga à aplicação e oferece filas de mensagens sem nenhum
servidor central (*broker*). Cada processo fala direto com o outro, e o que o
ZeroMQ esconde é a parte trabalhosa dos sockets — conexão, reconexão, *buffers*
e o enquadramento de cada mensagem.

## Contexto

O [módulo 02](../02-sockets/README.md) trabalhava com o socket cru: um fluxo de
bytes, sem fronteira entre uma mensagem e outra, e um `connect()` que falha se o
servidor ainda não subiu. O ZeroMQ troca isso por **mensagens inteiras**
(*frames*) e por **padrões de comunicação** prontos, cada um com o seu par de
tipos de socket:

| Padrão | Sockets | Relação | Onde |
|---|---|---|---|
| **Requisição-resposta** | `REQ` / `REP` | 1:1, alternância estrita | `exp6-1.py`, `exp6-6.py`, `exp6-7/` |
| **Publish-subscribe** | `PUB` / `SUB` | 1:N, filtro por tópico | `exp6-8/` |
| **Push-pull** | `PUSH` / `PULL` | N:N, distribuição de trabalho | — |

Comparado ao gRPC do [módulo 04](../04-grpc/README.md), o ZeroMQ não tem IDL nem
código gerado: ele entrega bytes, e o formato do que vai dentro é problema da
aplicação — qualquer um dos formatos do [módulo 03](../03-serialization/README.md)
serve.

## Estrutura

```
05-zmq/
├── exp6-1.py           # REQ-REP: o cliente manda HELO, o servidor responde
├── exp6-6.py           # REQ-REP em bytes: send/recv crus contra send_string/recv_string
├── exp6-7/             # Multipart: protocolo em duas etapas com vários frames
│   ├── server.py       #   OLEH + lista de operações, depois o cálculo
│   └── client.py       #   HELO, escolhe a operação, manda operação e valores
└── exp6-8/             # PUB-SUB: tópicos de A a D com valores aleatórios
    ├── server.py       #   Publica uma mensagem por segundo
    ├── client_a.py     #   Assina só o tópico A
    └── client_b.py     #   Assina o tópico vazio: recebe tudo
```

Os nomes seguem a numeração dos enunciados do experimento 6 (`exp6-<questão>`).

## Como executar

O módulo tem o seu próprio `.venv` (gitignored), só com o `pyzmq`:

```bash
cd 05-zmq
python3 -m venv .venv
.venv/bin/pip install pyzmq
```

O `argparse` dos enunciados já vem na biblioteca padrão; o pacote `argparse` do
PyPI é um *backport* antigo e não precisa ser instalado.

Em todos os exemplos o servidor fica em primeiro plano e o cliente vai num
segundo terminal:

```bash
.venv/bin/python exp6-1.py -s plymouth   # terminal 1
.venv/bin/python exp6-1.py               # terminal 2
```

```
Requesting HELO to tcp://localhost:5558
	- Hi from plymouth
```

```bash
.venv/bin/python exp6-6.py -s            # terminal 1: 12, b'Get the tip!'
.venv/bin/python exp6-6.py               # terminal 2: From server with love
```

```bash
cd exp6-7
../.venv/bin/python server.py                    # terminal 1
../.venv/bin/python client.py subtract 10 2.5    # terminal 2 (padrão: add 2 3)
```

```
Servidor: OLEH, operações: add,subtract
subtract(10, 2.5) = 7.5
```

```bash
cd exp6-8
../.venv/bin/python server.py       # terminal 1
../.venv/bin/python client_a.py     # terminal 2: b'A -15', b'A -34', …
../.venv/bin/python client_b.py     # terminal 3: todos os tópicos
```

**A porta é a 5558**, fora das do módulo 02 (50007) e do 04 (50051); os
servidores daqui disputam a mesma porta entre si, então um de cada vez. Todos
fazem *bind* em `localhost`, como o resto do repositório.

## Observações

### O cliente pode subir antes do servidor

Com o socket cru do módulo 02, rodar o cliente primeiro dá
`ConnectionRefusedError` na hora. No ZeroMQ o `connect()` não falha: a conexão
é tentada em segundo plano, o `send_string("HELO")` fica na fila local e o
cliente espera no `recv_string()`. Rodando o `exp6-1.py` nessa ordem, o cliente
imprimiu `Requesting HELO ...` e ficou bloqueado; quando o servidor subiu, a
mensagem foi entregue, a resposta voltou e o cliente terminou com status 0.

O servidor, por sua vez, **não** termina depois de responder: o `while True`
volta ao `recv_string()` à espera do próximo cliente, e só o Ctrl-C o encerra.

### REQ e REP exigem alternância estrita

O par `REQ`/`REP` é uma máquina de estados: o `REP` precisa de `recv` → `send`
→ `recv`, e o `REQ` de `send` → `recv` → `send`. Sair dessa ordem não trava —
levanta exceção na hora, dos dois lados:

```
REP recv sem responder: ZMQError - Operation cannot be accomplished in current state
REQ send sem receber:   ZMQError - Operation cannot be accomplished in current state
```

É uma armadilha no `exp6-1.py`: o servidor só responde se a mensagem for
`HELO`, então qualquer outra string o deixa sem resposta pendente, e o próximo
`recv_string()` derruba o servidor (o `except` só cobre o `KeyboardInterrupt`).
O servidor do `exp6-7/` responde **sempre**, inclusive com uma mensagem de erro
para operação desconhecida, valor inválido ou mensagem fora do protocolo.

### Tudo é byte; o resto é conveniência

O fio carrega o tamanho do *frame* seguido dos bytes. `send_string`,
`send_json`, `send_pyobj` e `send_multipart` (e os `recv_` correspondentes) são
camadas do `pyzmq` sobre o `send`/`recv` de bytes — outras linguagens podem não
ter as mesmas. O `exp6-6.py` mostra que as duas pontas não precisam usar o
mesmo par: o servidor recebe com `recv()` e vê `12, b'Get the tip!'`, responde
com `send("...".encode())`, e o cliente lê com `recv_string()`.

O `send_pyobj`/`recv_pyobj` usa `pickle`, e por isso carrega o mesmo aviso do
[módulo 03](../03-serialization/README.md): desserializar dado não confiável é
executar código de quem mandou.

### Multipart: uma mensagem, vários frames

No `exp6-7/`, cada etapa do protocolo é **uma** mensagem com vários *frames*. O
`send_multipart([b"OLEH", b"add,subtract"])` marca todos os *frames* menos o
último com `SNDMORE`, e o `recv_multipart()` só retorna quando a mensagem inteira
chegou — a entrega é atômica, ou chegam todos os *frames* ou nenhum.

O servidor não guarda em que etapa cada cliente está: ele decide pelo conteúdo
(`["HELO"]` é o *handshake*, três *frames* são um cálculo). Assim dois clientes
intercalados não se confundem, mesmo o `REP` atendendo um de cada vez.

### PUB-SUB: o filtro é um prefixo, e quem chega tarde perde

A assinatura compara os **primeiros bytes** da mensagem com o tópico, e o `recv`
devolve a mensagem inteira, tópico incluído. O `client_a.py` assina `b'A'` e
recebe só `b'A -15'`, `b'A -34'`…; o `client_b.py` assina `b''`, que é prefixo de
tudo. Por ser prefixo, `b'A'` também casaria com um tópico `AB`; aqui não há
ambiguidade porque os tópicos têm uma letra só.

O `PUB` não espera assinante nem guarda mensagem para quem ainda não chegou.
Rodando o servidor e os dois clientes juntos, o `client_b.py` perdeu a primeira
mensagem publicada (`C -33`). Medindo isolado, um `SUB` que conecta e assina
logo antes de cinco publicações não recebeu nenhuma delas — só a publicada 0,3 s
depois. É o *slow joiner*: a conexão e o registro da assinatura levam tempo, e o
que for publicado nesse intervalo se perde. Em `REQ`/`REP` isso não acontece,
porque a requisição espera na fila até ser entregue.

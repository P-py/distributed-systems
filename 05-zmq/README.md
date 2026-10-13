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
| **Publish-subscribe** | `PUB` / `SUB` | 1:N, filtro por tópico | `exp6-8/`, `exp7_6/` |
| **Push-pull** | `PUSH` / `PULL` | N:N, distribuição de trabalho | `exp7_3/` |

O `exp7_7/` combina dois deles: um agregador pergunta a todas as locadoras por
`PUB`/`SUB` e recolhe as respostas por `REQ`/`REP`.

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
├── exp6-8/             # PUB-SUB: tópicos de A a D com valores aleatórios
│   ├── server.py       #   Publica uma mensagem por segundo
│   ├── client_a.py     #   Assina só o tópico A
│   └── client_b.py     #   Assina o tópico vazio: recebe tudo
├── exp7_3/             # PUSH-PULL: o "Divide and Conquer" do guia do ZeroMQ
│   ├── taskvent.py     #   Ventilador: distribui 100 tarefas de 1–100 ms
│   ├── taskwork.py     #   Worker: executa a tarefa e avisa o sink
│   └── tasksink.py     #   Sink: junta os 100 resultados e mede o tempo
├── exp7_6/             # PUB-SUB multipart: tópico no 1º frame, Person no 2º
│   ├── person.proto    #   Person(name, height, luck_numbers)
│   ├── person_pb2.py   #   Gerado pelo protoc (versionado)
│   ├── server.py       #   Publica cada pessoa em protobuf e em JSON, a cada 1 s
│   ├── client_proto.py #   Assina o tópico protob
│   └── client_json.py  #   Assina o tópico json
└── exp7_7/             # Agregador de locadoras de carros (esboço, execução única)
    ├── aggregator.py   #   PUB manda QTY; REP recebe as listas e responde ACK
    ├── rental_a.py     #   SUB recebe QTY; REQ manda URL da API + carros livres
    └── rental_b.py     #   Cópia do rental_a com outra frota e outra URL
```

Os nomes seguem a numeração dos enunciados (`exp6-<questão>` e
`exp7_<questão>`), e as pastas mantêm o formato em que cada exercício é
entregue.

> **Dados de amostra.** As pessoas do `exp7_6/` (`Alan Turing`, `Ada Lovelace`,
> `Grace Hopper`) e as frotas e URLs do `exp7_7/` (domínio `.example`, reservado
> para exemplos) são fictícias; a versão entregue com dado real fica fora do
> repositório.

## Como executar

O módulo tem o seu próprio `.venv` (gitignored) com o `pyzmq` e o
`grpcio-tools` — este só por causa do `exp7_6/`, que precisa do runtime do
`protobuf` (5.x, que vem junto) e do `protoc` para regerar o `person_pb2.py`:

```bash
cd 05-zmq
python3 -m venv .venv
.venv/bin/pip install pyzmq grpcio-tools
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

O `exp7_3/` precisa de três papéis no ar antes de começar: o sink, quantos
workers se quiser, e só então o ventilador — que espera o Enter justamente para
dar tempo de os workers conectarem:

```bash
cd exp7_3
../.venv/bin/python tasksink.py     # terminal 1
../.venv/bin/python taskwork.py     # terminais 2 e 3: um por worker
../.venv/bin/python taskvent.py     # terminal 4: Enter com os workers no ar
```

```
Custo total esperado: 4811 ms                 ← taskvent: soma das 100 tarefas
:.........:.........(…)Tempo total decorrido: 2538 ms   ← tasksink, com 2 workers
```

```bash
cd exp7_6
../.venv/bin/python client_proto.py   # terminal 1
../.venv/bin/python client_json.py    # terminal 2
../.venv/bin/python server.py         # terminal 3
```

```
Nome: Ada Lovelace
Altura: 1.68
Sorte:[2, 11, 29]
```

O `person_pb2.py` está versionado; só precisa ser regerado quando o
`person.proto` mudar:

```bash
cd exp7_6
../.venv/bin/python -m grpc_tools.protoc -I. --python_out=. person.proto
```

O `exp7_7/` roda uma vez e termina, em qualquer ordem — o agregador repete o
`QTY` a cada segundo até as duas locadoras responderem:

```bash
cd exp7_7
../.venv/bin/python rental_a.py       # terminal 1
../.venv/bin/python rental_b.py       # terminal 2
../.venv/bin/python aggregator.py     # terminal 3
```

```
https://api.locadora-a.example/v1/aluguel: 3 carro(s) disponível(is)
  2022/Fiat/Argo - R$ 129.90/dia
  2021/Chevrolet/Onix - R$ 119.90/dia
  2024/Toyota/Corolla - R$ 249.90/dia
https://api.locadora-b.example/v1/aluguel: 3 carro(s) disponível(is)
  …
2 de 2 locadora(s) responderam
```

**As portas** ficam fora das do módulo 02 (50007) e do 04 (50051):

| Porta | Quem faz *bind* |
|---|---|
| 5557 | `exp7_3/taskvent.py` |
| 5558 | `exp6-1.py`, `exp6-6.py`, `exp6-7/`, `exp6-8/`, `exp7_3/tasksink.py`, `exp7_6/` |
| 5560, 5561 | `exp7_7/aggregator.py` (PUB e REP) |

Os exercícios que dividem a 5558 rodam um de cada vez. Todos fazem *bind* em
`localhost`, como o resto do repositório.

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

### PUSH-PULL: o trabalho só é dividido entre quem já chegou

O `PUSH` entrega cada mensagem a **um** `PULL`, em rodízio (*round-robin*) — ao
contrário do `PUB`, que entrega uma cópia a cada assinante. Com dois workers
conectados, as 100 tarefas do `exp7_3/` se dividem 50/50 e o lote leva perto de
metade da soma das tarefas:

| Rodada | Tarefas por worker | Custo esperado (soma) | Tempo medido no sink |
|---|---|---|---|
| Enter na hora | **100 / 0** | 5240 ms | 5690 ms |
| Enter 1 s depois | 50 / 50 | 5493 ms | 2949 ms |
| Enter 1 s depois | 50 / 50 | 4811 ms | 2538 ms |

A primeira linha é o motivo do "Pressione Enter": o `PUSH` só reparte entre os
`PULL` **já conectados** quando a mensagem sai. Com o Enter imediato, o segundo
worker ainda não tinha terminado de conectar, e o primeiro levou o lote inteiro
— o tempo ficou o de um worker só. Nas outras, o tempo fica um pouco acima da
metade (53–54%): o rodízio iguala o **número** de tarefas, não a soma dos
milissegundos de cada worker, e o sink só para quando o mais lento termina.

O rodízio também não olha para a carga: um worker lento recebe tantas tarefas
quanto um rápido, e uma tarefa entregue a um worker que morre se perde.

### Multipart como tópico: o filtro olha só o primeiro frame

No `exp7_6/`, cada publicação é `[b"protob", payload]` ou `[b"json", payload]`.
A assinatura compara o prefixo do **primeiro** *frame*, então o conteúdo binário
do protobuf nunca é confundido com um tópico, e cada cliente recebe só o seu
canal. O mesmo `Person` nos dois formatos, montado a partir do mesmo `dict`:

| Pessoa | protobuf | JSON |
|---|---|---|
| Alan Turing | 27 bytes | 68 bytes |
| Ada Lovelace | 28 bytes | 69 bytes |
| Grace Hopper | 28 bytes | 68 bytes |

**`height` é `double` no `.proto`, não `float`.** O `float` do Python tem 64
bits; com o `float` de 32 bits do proto, o cliente protobuf imprimiria
`Altura: 1.7699999809265137` enquanto o JSON imprime `1.77` — o mesmo efeito
medido no [módulo 03](../03-serialization/README.md#o-que-quebra-na-volta).

O *slow joiner* aparece de novo: mesmo com os dois clientes no ar antes do
servidor, os dois perderam a primeira pessoa, publicada logo depois do `bind`;
do segundo ciclo em diante chega tudo.

**O `person_pb2.py` exige o runtime `protobuf` 5.29 ou mais novo** (ele confere
a versão ao ser importado). É outro par gerador/runtime, diferente do
`03-serialization`, que está preso no 3.20.3 — mais um motivo para cada módulo
ter o seu venv.

### O agregador: PUB para perguntar, REQ/REP para responder

O `exp7_7/` é o esboço de um agregador de locadoras. O agregador não conhece as
locadoras: publica `QTY` no `PUB`, e cada locadora que assinou responde por
conta própria pelo `REQ`, com dois *frames* — a URL da sua API (fictícia) e,
via `send_pyobj`, a tupla `(quantidade, [(nome, valor), …])` com os carros não
alugados. O agregador responde `ACK` a cada uma pelo `REP`.

Como um `QTY` publicado logo depois do `bind` se perderia (o *slow joiner* de
novo), o agregador **repete o `QTY` a cada segundo** até as duas locadoras
responderem, com um limite de 10 tentativas. Assim os três scripts podem subir
em qualquer ordem — testado com as locadoras antes e com o agregador antes. Uma
locadora que já respondeu não responde duas vezes: depois do `ACK` ela termina.

O enunciado chama o exercício de ROUTER-DEALER, mas descreve `PUB`/`SUB` e
`REQ`/`REP`, e é isso que está implementado. O `REQ` e o `REP` são, por dentro,
um `DEALER` e um `ROUTER` com o envelope tratado automaticamente; trocar o `REP`
do agregador por um `ROUTER` é o passo natural quando ele precisar atender várias
locadoras ao mesmo tempo, em vez de uma resposta por vez.

O `send_pyobj` é permitido aqui porque as duas pontas são Python, mas o
`recv_pyobj` do agregador faz `pickle.loads` em tudo que chega à porta 5561 —
o mesmo risco do [módulo 03](../03-serialization/README.md): em `localhost`, num
esboço, tudo bem; exposto na rede, o formato precisa ser JSON ou protobuf.

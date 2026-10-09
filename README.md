# Lab de Programação Distribuída

Laboratório pessoal de **comunicação entre processos (IPC)** e **programação
distribuída**, em Python (e um pouco de Java).

## Sobre

Distribuir uma aplicação em processos separados — por desempenho ou por
isolamento/segurança — só faz sentido se esses processos conseguirem conversar.
O sistema operacional oferece três caminhos para isso, e cada módulo deste
repositório percorre um deles, do compartilhamento de páginas de memória entre
processos da mesma máquina até chamadas de procedimento remoto pela rede:

| Mecanismo | Base do S.O. | Onde |
|---|---|---|
| **Pipe** | Sistema de arquivos virtual | — |
| **Memória compartilhada** (SHM) | MMU compartilhando páginas de memória | [01-shared-memory](01-shared-memory/) |
| **Sockets** (e Unix Domain Sockets) | APIs de comunicação de rede | [02-sockets](02-sockets/) |

A diferença prática entre eles é o alcance. SHM é o mecanismo mais direto e
rápido, mas vive dentro de **uma máquina**; sockets custam mais, porém colocam
os processos em **máquinas diferentes** com a mesma API — e é sobre eles que se
constroem as camadas seguintes, do HTTP ao RPC.

Escolhido o canal, resta a pergunta de **o que trafega por ele**: um objeto na
memória de um processo precisa virar uma sequência de bytes para atravessar o
canal e voltar a ser objeto do outro lado. É a **serialização**, tema do
[03-serialization](03-serialization/). Com o canal e o formato resolvidos, o
[04-grpc](04-grpc/) fecha o caminho: uma IDL descreve o **serviço**, e a chamada
remota passa a ser código gerado. O [05-zmq](05-zmq/) volta um passo e troca a
chamada pela **mensagem**: filas embutidas na aplicação, sem *broker*, em
padrões de requisição-resposta e publish-subscribe.

## Módulos

| # | Tema | Assuntos |
|---|---|---|
| [**01-shared-memory**](01-shared-memory/README.md) | Memória compartilhada | `shared_memory`, semáforos, condição de corrida, NumPy, `Manager` |
| [**02-sockets**](02-sockets/README.md) | Sockets, HTTP e XML-RPC | TCP, `listen()`/`accept()`, concorrência com threads, HTTP, RPC |
| [**03-serialization**](03-serialization/README.md) | Serialização | Formatos nativos, JSON e Protocol Buffers entre Java e Python |
| [**04-grpc**](04-grpc/README.md) | Chamada de procedimento remoto | IDL com `service`, stubs gerados, status de erro, HTTP/2 |
| [**05-zmq**](05-zmq/README.md) | Mensageria embutida | ZeroMQ, `REQ`/`REP`, multipart, `PUB`/`SUB` com tópicos |

<details>
<summary><b>01 — Memória compartilhada</b></summary>

IPC pela via mais direta: dois processos enxergando a mesma região de memória,
como *threads* fazem dentro de um processo. Com isso vem o problema do controle
de acesso — o equivalente ao *mutex* entre processos é o **semáforo**.

- `shm_semaphore.py` — SHM + semáforo, medindo o tempo de aquisição e de leitura/escrita
- `shm_numpy_histogram.py` — SHM + NumPy, cálculo de histograma sobre *views* `ndarray`
- `manager_producer_consumer.py` — `Manager` de alto nível, produtor/consumidor com `Event`

→ [detalhes em `01-shared-memory/README.md`](01-shared-memory/README.md)

</details>

<details>
<summary><b>02 — Sockets, HTTP e XML-RPC</b></summary>

A partir de um *echo server* TCP mínimo, o módulo sobe uma camada por vez: a
**fila de espera** do `listen()` e o atendimento concorrente, o **HTTP** como
protocolo sobre esses sockets, e o **XML-RPC** usando o HTTP como transporte
para expor funções a processos externos.

- `tcp_echo.py` — *backlog* do `listen()`, `accept()` e uma thread por conexão
- `http_get.py` — servidor HTTP tratando uma requisição GET
- `xmlrpc_math.py` — serviço XML-RPC expondo `pow`, `add` e `mul`
- `task_service_server.py` / `task_service_client.py` — lista de tarefas com cliente de validação

→ [detalhes em `02-sockets/README.md`](02-sockets/README.md)

</details>

<details>
<summary><b>03 — Serialização</b></summary>

O mesmo objeto `Person` atravessando três formatos: os **nativos** de cada
linguagem (o `ObjectOutputStream` do Java e o `pickle` do Python), que não se
cruzam; o **JSON**, que leva o objeto de uma linguagem para a outra ao custo de
não verificar nada; e o **Protocol Buffers**, que recupera o esquema e a
eficiência do binário a partir de uma IDL.

- `native/` — ida e volta em cada formato nativo, com validação por re-serialização
- `json/` — duas aplicações (Java com Gson e Python) trocando o mesmo objeto nos dois sentidos
- `protobuf/` — a IDL do `Person`, o código gerado pelo `protoc` e a travessia
  Python → Java sobre o stream binário em base64

→ [detalhes em `03-serialization/README.md`](03-serialization/README.md)

</details>

<details>
<summary><b>04 — gRPC</b></summary>

O RPC com as três peças juntas: a IDL do módulo 03 descrevendo também o
**serviço**, o Protocol Buffers como formato e o HTTP/2 como transporte. Um
`ContactsManager` faz o CRUD do `Person` em memória, e o cliente percorre o
roteiro de criar, buscar, remover e tentar buscar o que não existe mais.

- `contact_book.proto` — o `service` com as três rpc e as mensagens de cada uma
- `server.py` — o *servicer* com `ThreadPoolExecutor`, `lock` no estado e status de erro
- `client.py` — os cinco passos, com `try/except grpc.RpcError` no último

→ [detalhes em `04-grpc/README.md`](04-grpc/README.md)

</details>

<details>
<summary><b>05 — Mensageria com ZeroMQ</b></summary>

Mensagens em vez de chamadas, sem servidor central: o ZeroMQ cuida da conexão,
da reconexão e do enquadramento, e a aplicação escolhe o padrão. O módulo sai
de um `HELO` em requisição-resposta, desce aos bytes por baixo das conveniências
do `pyzmq`, monta um protocolo de duas etapas com mensagens de vários *frames* e
termina num publish-subscribe filtrado por tópico.

- `exp6-1.py` / `exp6-6.py` — `REQ`/`REP` com strings e com bytes crus
- `exp6-7/` — calculadora com `send_multipart`/`recv_multipart`
- `exp6-8/` — publicador de tópicos `A`–`D` e dois assinantes (um tópico e todos)

→ [detalhes em `05-zmq/README.md`](05-zmq/README.md)

</details>

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install numpy              # necessário apenas para o shm_numpy_histogram.py
```

Cada módulo traz seus próprios comandos: veja a seção **Como executar** do
[01](01-shared-memory/README.md#como-executar), do
[02](02-sockets/README.md#como-executar), do
[03](03-serialization/README.md#como-executar), do
[04](04-grpc/README.md#como-executar) ou do
[05](05-zmq/README.md#como-executar) — o 03 inclui os passos de compilação da
parte em Java, e o 04 e o 05 têm cada um o seu próprio venv.

## Requisitos

- **Python 3.8+**
- **NumPy** — apenas para o `shm_numpy_histogram.py`
- **JDK 11+** — apenas para as partes em Java do módulo 03
- **grpcio / grpcio-tools** — apenas para o módulo 04, no `.venv` dele
- **pyzmq** — apenas para o módulo 05, no `.venv` dele
- **Gson 2.13.1** — apenas para `03-serialization/json`; o `run.sh` baixa o jar
- **protobuf 3.6.1** — para `03-serialization/protobuf`: o `run.sh` baixa o jar e
  instala o runtime do Python no venv do módulo, nas versões do `protoc` que gerou
  o código
- **protoc 3.6+** — apenas para regerar o código de `03-serialization/protobuf`
- **Linux/Unix** (ou WSL no Windows) — o módulo 01 depende de `os.fork()` e da
  semântica de SHM do POSIX

## Licença

Distribuído sob os termos do arquivo [LICENSE](LICENSE).

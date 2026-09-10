# Lab de Programação Distribuída

Módulos de **sistemas distribuídos** e **comunicação entre processos (IPC)**
em Python.

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

## Módulos

| # | Tema | Assuntos |
|---|---|---|
| [**01-shared-memory**](01-shared-memory/README.md) | Memória compartilhada | `shared_memory`, semáforos, condição de corrida, NumPy, `Manager` |
| [**02-sockets**](02-sockets/README.md) | Sockets, HTTP e XML-RPC | TCP, `listen()`/`accept()`, concorrência com threads, HTTP, RPC |

<details>
<summary><b>01-shared-memory — Memória Compartilhada</b></summary>

IPC pela via mais direta: dois processos enxergando a mesma região de memória,
como *threads* fazem dentro de um processo. Com isso vem o problema do controle
de acesso — o equivalente ao *mutex* entre processos é o **semáforo**.

- `shm_semaphore.py` — SHM + semáforo, medindo o tempo de aquisição e de leitura/escrita
- `shm_numpy_histogram.py` — SHM + NumPy, cálculo de histograma sobre *views* `ndarray`
- `manager_producer_consumer.py` — `Manager` de alto nível, produtor/consumidor com `Event`

→ [detalhes em `01-shared-memory/README.md`](01-shared-memory/README.md)

</details>

<details>
<summary><b>02-sockets — Sockets, HTTP e XML-RPC</b></summary>

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

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install numpy              # necessário apenas para o shm_numpy_histogram
```

Cada módulo traz seus próprios comandos: veja a seção **Como executar** do
[01-shared-memory](01-shared-memory/README.md#como-executar) ou do [02-sockets](02-sockets/README.md#como-executar).

## Requisitos

- **Python 3.8+**
- **NumPy** — apenas para o `shm_numpy_histogram.py`
- **Linux/Unix** (ou WSL no Windows) — o 01-shared-memory depende de `os.fork()` e da
  semântica de SHM do POSIX

## Licença

Distribuído sob os termos do arquivo [LICENSE](LICENSE).

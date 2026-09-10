# Lab de Programação Distribuída

Módulos de **sistemas distribuídos** e **comunicação entre processos (IPC)**
em Python.

## Módulo 2 — Memória Compartilhada

Este módulo explora a **comunicação entre processos (IPC)** usando
**memória compartilhada** (`shared_memory`), sincronização com **semáforos** e
gerenciadores de alto nível (`Manager` / `SharedMemoryManager`).

### Contexto

Para distribuir a lógica de uma aplicação em processos separados — seja por
desempenho ou por isolamento/segurança — existem três caminhos principais:

| Mecanismo | Base do S.O. |
|---|---|
| **Pipe** | Sistema de arquivos virtual |
| **Sockets** (e Unix Domain Sockets) | APIs de comunicação de rede |
| **Memória Compartilhada** (SHM) | MMU compartilhando páginas de memória |

Dentre elas, a **Memória Compartilhada (SHM)** é o mecanismo mais eficaz e
direto, aproximando-se da forma como *threads* compartilham a mesma região de
memória do processo.

Pontos-chave:

- Assim como *threads* precisam de *mutexes*, a SHM precisa de controle para
  evitar colisão e condição de corrida. O equivalente ao *mutex* entre
  processos é o **Semáforo**.
- É possível compartilhar memória entre processos de **linguagens diferentes**,
  desde que se usem tipos de dados intercambiáveis.
- Em Python, a biblioteca `multiprocessing` encapsula os recursos do S.O.:
  `shared_memory` (SHM) e `Semaphore`/`Lock`. Objetos de alto nível como os
  `Manager` (`multiprocessing.managers`) cuidam da sincronização e do
  processamento distribuído entre processos Python.
- Não é obrigatório dar um **nome** ao construtor da memória compartilhada.
  Com `fork`, o processo filho herda a SHM se ela for passada como argumento.
- No Unix/Linux também é possível criar um arquivo em `/dev/shm` e usar seu
  *file descriptor* (fd) como "nome", via `mmap` (também herdável pelos filhos).

> **Nota:** frameworks de alto nível como a JVM (Java) e o .NET Framework (C#)
> também oferecem recursos de sincronização entre processos da mesma linguagem.

### Estrutura

```
01-shared-memory/
├── shm_semaphore.py       # SHM + Semáforo (leitura/escrita, medição de tempo)
├── shm_numpy_histogram.py       # SHM + NumPy (cálculo de histograma)
└── manager_producer_consumer.py       # Managers (produtor/consumidor com Value/Event)
```

### Módulos

#### `shm_semaphore.py` — SHM e Semáforo: medindo o tempo de acesso

Um processo **supervisor** é dono dos recursos compartilhados. Ele cria a
memória compartilhada e o semáforo e, via `os.fork()`, gera dois subprocessos:
um **leitor** (`'r'`) e um **escritor** (`'w'`).

- `MEM_BLOCK_NAME = "mem_block"` e `MEM_BLOCK_SIZE = 64` funcionam como
  *macros* (`#define`) do script.
- Cada filho executa `do_child_work(sem, mode)`, repetindo 1000 vezes:
  1. Adquire o semáforo (`acquire`) — mede o tempo de aquisição.
  2. Lê (`bytes(shm.buf)`) ou escreve (`shm.buf[:] = ...`) — mede o tempo da
     operação.
  3. Libera o semáforo (`release`).
- Ao final imprime os **tempos médios** de aquisição e de operação (dica de
  formatação: `{:.2e}` para notação científica).
- O supervisor aguarda os filhos com `os.waitpid` e sempre libera a SHM com
  `.close()` **e** `.unlink()`.

> Observação: aumentando o tamanho do bloco, os tempos ficam na casa dos
> microssegundos. Valores maiores que o tamanho de uma página (~4 KB) começam a
> impactar mais o tempo de execução.

#### `shm_numpy_histogram.py` — SHM e NumPy: cálculo de histograma

Requer **NumPy**. O `main` cria duas memórias compartilhadas *anônimas* e
suas *views* `ndarray`:

- **Dados** — 512 elementos `np.uint8` (tamanho total: 512 bytes).
- **Histograma** — 16 elementos `np.uint` (16 × 8 = 128 bytes).

Um único processo filho (`multiprocessing.Process`) calcula o histograma de
16 *bins* no intervalo de bytes `0–255` (`np.histogram`, usando apenas o
primeiro array retornado).

> Como leitura e escrita usam arrays distintos e há apenas um processo filho,
> não é necessário semáforo/trava.
>
> **Eficiência:** o Python trata o *buffer* como leitura; a escrita deve ser
> explícita via *subscribe* de array — ex.: `arr[:] = ...`.

#### `manager_producer_consumer.py` — Managers: produtor/consumidor

Usa um gerenciador de alto nível que cuida da sincronização de objetos Python
entre instâncias (`Value`, `Event`, `ShareableList`).

- **`producer(shl, idx, dirty)`** — sorteia 10 vezes uma posição (0–2) e um
  valor (0–999), grava na `ShareableList`, atualiza `idx`, dispara o `Event` e
  espera enquanto ele continuar setado (`while dirty.is_set(): dirty.wait(0.1)`).
- **`consumer(shl, idx, dirty)`** — em 10 iterações, aguarda a notificação,
  copia o índice modificado, imprime a posição/valor/lista e libera o evento.
- **`main`** — cria um `Manager` (evento + índice) e um `SharedMemoryManager`
  (`ShareableList` de três zeros), inicia consumidor e produtor e aguarda ambos.

> Todo o gerenciamento, comunicação e serialização é feito pelos `Manager`.
> Filas (`Queue`) são outra opção, mas prendem todos os processos à mesma
> versão de Python.

### Como executar

```bash
# a partir da raiz do repositório
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install numpy              # necessário para o shm_numpy_histogram

cd 01-shared-memory
python shm_semaphore.py
python shm_numpy_histogram.py
python manager_producer_consumer.py
```

> **Plataforma:** os exemplos dependem de `os.fork()` e da semântica de SHM do
> POSIX; execute em **Linux/Unix** (ou WSL no Windows).

### Requisitos

- Python 3.8+
- NumPy (apenas para `shm_numpy_histogram.py`)

## Módulo 3 — Sockets e HTTP

Este módulo explora a comunicação entre processos usando a **API de redes
(sockets)**: o comportamento da **fila de espera** do `listen()` e, subindo de
nível, o **HTTP** construído sobre esses sockets e o **XML-RPC** construído
sobre o HTTP.

### Contexto

Uma aplicação pode conversar com outra por qualquer mecanismo de IPC, mas a
forma mais prevalente é a **API de redes (sockets)**: com ela os processos podem
estar em **máquinas diferentes** (IPs distintos), além do caso local
(`localhost` / `127.0.0.1`). A API de sockets é **padronizada** e está
disponível em sistemas operacionais e linguagens diferentes.

O ponto de partida é um par cliente/servidor TCP mínimo (*echo server*),
selecionado pelo argumento `-s`/`--server`:

- **Servidor** — `socket()` → `bind()` → `listen(1)` → `accept()` e, para a
  conexão aceita, um laço `recv()`/`sendall()` até o cliente fechar.
- **Cliente** — `socket()` → `connect()` → `sendall()` → `recv()`.

> Requer a lib `argparse` no `.venv`.

### Estrutura

```
02-sockets/
├── tcp_echo.py           # Echo server TCP: backlog do listen() e threads
├── http_get.py           # Servidor HTTP: tratando uma requisição GET
├── xmlrpc_math.py           # XML-RPC: expondo funções sobre o HTTP
├── task_service_server.py    # Lista de tarefas: serviço XML-RPC
└── task_service_client.py    # Lista de tarefas: teste de validação da interface
```

### Módulos

#### `tcp_echo.py` — fila de espera e atendimento concorrente

O script estende o exemplo base com o que é preciso para observar a fila:

- `DELAY = 5` — atraso artificial (`time.sleep`) **no tratamento da
  requisição**, antes de responder, simulando processamento demorado.
- `-b/--backlog N` — o argumento do `listen()`.
- `-1/--serial` — servidor sem threads (comportamento original).
- `-n/--clients N` — dispara N requisições **simultâneas** (uma thread por
  cliente), imprimindo o tempo de retorno do `connect()` e do `recv()`.

**Observação 1 — `listen(1)` vs. `listen(2)`, servidor serial, 2 clientes.**
O resultado é idêntico nos dois casos: um cliente responde em ~5 s e o outro em
~10 s. O detalhe importante é que **os dois `connect()` retornam
imediatamente**, mesmo antes de o servidor chamar `accept()`:

```
client-2: connect() retornou em 0.00s
client-1: connect() retornou em 0.00s
client-2: Received b'Hello, world' em 5.03s
client-1: Received b'Hello, world' em 10.03s
```

Quem completa o *three-way handshake* é o **kernel**, que deposita a conexão
pronta na **fila de espera** (*accept queue*); o `accept()` apenas retira dela.
Por isso o cliente enfileirado não recebe erro nem bloqueia na conexão — ele
bloqueia no `recv()`, esperando a vez.

**Observação 2 — quando o backlog importa.** Com 2 clientes a fila nem chega a
encher, daí `listen(1)` e `listen(2)` serem indistinguíveis. O efeito aparece ao
estourar o backlog (`listen(1)` com 4 clientes):

```
client-1/2/3: connect() retornou em 0.00s
client-4:     connect() retornou em 5.11s   <- SYN descartado, cliente retransmitiu
```

Ou seja, o argumento do `listen()` dimensiona a fila de conexões **já
estabelecidas e ainda não aceitas** (no Linux, `backlog` mais a que está sendo
aceita). Com a fila cheia, o kernel descarta o SYN e o cliente só entra quando o
servidor libera espaço. Nada disso acelera o atendimento: em modo serial é
sempre um por vez — 5 s, 10 s, 15 s, 20 s.

**Alteração — uma thread por conexão.** O tratamento da requisição foi extraído
para `handle(conn, addr)` e o laço do servidor passa a delegá-lo a uma thread,
voltando imediatamente ao `accept()`:

```python
conn, addr = s.accept()
threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
```

Com isso, os dois clientes são atendidos em paralelo (~5 s cada), mesmo com
`listen(1)`:

```
server: Connected by ('127.0.0.1', 35318)
server: Connected by ('127.0.0.1', 35320)   <- accept() volta na hora
client-2: Received b'Hello, world' em 5.01s
client-1: Received b'Hello, world' em 5.03s
```

Dois detalhes de apoio: `daemon=True` para o servidor encerrar com Ctrl-C sem
esperar as threads, e `SO_REUSEADDR` para permitir reiniciar o servidor sem
aguardar o `TIME_WAIT` da porta.

#### `http_get.py` — HTTP: tratando uma requisição GET

O **HTTP** nasceu para o transporte de arquivos — inicialmente o HTML e os
demais recursos que compunham uma página. Na prática, é uma forma **básica de
RPC** (chamada de procedimento remoto): implementa alguns comandos, ou
**verbos** (`GET`, `HEAD`, `POST`, `PUT` etc.), e cada um deles tem um **padrão
de texto (e bytes)** que descreve a mensagem enviada ao servidor, a qual
desencadeia um processamento e gera uma mensagem de resposta.

A biblioteca padrão do Python já traz esse protocolo pronto sobre os sockets do
módulo anterior, em `http.server`:

- **`BaseHTTPRequestHandler`** — recebe a conexão já aceita, faz o *parsing* da
  linha de requisição e dos cabeçalhos, e despacha para o método
  `do_<VERBO>` correspondente. Tratar o GET é implementar `do_GET`; um verbo
  sem método definido recebe `501 Unsupported method`.
- **`HTTPServer`** — cuida de `bind()`/`listen()`/`accept()`; `serve_forever()`
  é o laço de aceitação.

Dentro do `do_GET`, a resposta é montada em três passos: `send_response(200)`
escreve a linha de status, `end_headers()` fecha o bloco de cabeçalhos e a
linha em branco que o separa do corpo, e `self.wfile.write(b'Hello, world!')`
grava o corpo — `wfile` é o *file object* de escrita do socket, e por isso
recebe **bytes**, não `str`.

A troca completa, capturada com um cliente de socket cru (o mesmo padrão que o
navegador ou o `curl` produzem):

```http
GET /teste?x=1 HTTP/1.1
Host: localhost:50007
User-Agent: raw-socket

--- resposta ---
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.8.10
Date: Thu, 10 Sep 2026 00:29:24 GMT

Hello, world!
```

Note que o caminho e a *query string* são ignorados: **qualquer** GET cai no
mesmo `do_GET` e recebe a mesma resposta (`self.path` é quem traria
`/teste?x=1`). Note também o `HTTP/1.0` na resposta — o padrão do
`BaseHTTPRequestHandler`, que fecha a conexão a cada requisição.

> Assim como o servidor serial do `tcp_echo.py`, o `HTTPServer` atende **uma
> requisição por vez**; a versão concorrente equivalente é o
> `ThreadingHTTPServer`.

#### `xmlrpc_math.py` — XML-RPC: expondo funções sobre o HTTP

O **XML-RPC** foi uma forma simplificada de usar a **infraestrutura do HTTP**
para **expor funções** de uma aplicação ao acesso de processos externos. Se o
HTTP já é um RPC básico com verbos fixos, o XML-RPC usa esse transporte para
carregar a chamada de verdade: um `POST` cujo corpo é um XML com o **nome do
método** e seus **parâmetros**, e cuja resposta é o **valor de retorno** — tudo
sobre a mesma porta e o mesmo protocolo do etapa anterior.

**Servidor** (`SimpleXMLRPCServer`) — três formas de registrar o que é exposto:

```python
server.register_introspection_functions()  # habilita system.listMethods etc.
server.register_function(pow)              # função padrão do Python

@server.register_function(name='add')      # nome diferente do original
def adder_function(x, y): return x + y

@server.register_function                  # pelo próprio function.__name__
def mul(x, y): return x * y
```

**Cliente** (`xmlrpc.client.ServerProxy`) — o proxy traduz **atributo acessado
em nome de método remoto**: escrever `proxy.pow(2, 9)` não resolve nada
localmente, apenas serializa a chamada e a envia. Daí a ilusão de estar
chamando uma função local:

```
call pow(2,9) 512
call add(1,2) 3
call mul(-5,20) -100
```

Note que `adder_function` foi chamada como `add` — quem vale é o nome de
registro, não o nome em Python.

**A mensagem por baixo.** Reproduzindo a chamada `pow(2, 9)` com um socket cru,
fica visível que é HTTP comum transportando XML:

```http
POST /RPC2 HTTP/1.1                    HTTP/1.0 200 OK
Host: localhost:50007                  Server: BaseHTTP/0.6 Python/3.8.10
Content-Type: text/xml            →    Content-type: text/xml
Content-Length: 187                    Content-length: 123

<?xml version='1.0'?>                  <?xml version='1.0'?>
<methodCall>                           <methodResponse>
<methodName>pow</methodName>           <params>
<params>                               <param>
<param>                                <value><int>512</int></value>
<value><int>2</int></value>            </param>
</param>                               </params>
<param>                                </methodResponse>
<value><int>9</int></value>
</param>
</params>
</methodCall>
```

Aqui o corpo é **obrigatório** nos dois sentidos — é ele que carrega a chamada e
o retorno —, e a tipagem é explícita no XML (`<int>`), o que permite ao outro
lado reconstruir o valor na sua própria linguagem.

**Introspecção.** `register_introspection_functions()` acrescenta métodos
`system.*` que permitem ao cliente perguntar o que existe do outro lado:

```
listMethods: ['add', 'mul', 'pow', 'system.listMethods',
              'system.methodHelp', 'system.methodSignature']
methodHelp(pow): Equivalent to base**exp with 2 arguments or base**exp % mod ...
```

**Erros** viram *faults*, não exceções locais: chamar um método não registrado
levanta `xmlrpc.client.Fault` no cliente — `Fault 1 - <class 'Exception'>:method
"div" is not supported` —, com o servidor continuando de pé.

#### `task_service_server.py` / `task_service_client.py` — lista de tarefas

Uma aplicação completa em dois arquivos: um **serviço** XML-RPC de lista de
tarefas e um **cliente que valida a interface**.

**Servidor.** Mantém as tarefas em um dicionário na memória, com os campos
`id`, `title`, `created_at`, `finished_at` e `description`, e expõe cinco
métodos:

| Método | Papel |
|---|---|
| `create_task(title, description='')` | Cria a tarefa aberta e devolve o registro |
| `finish_task(id)` | Carimba `finished_at` e devolve o registro atualizado |
| `list_all()` | Todas as tarefas |
| `list_open()` | Só as abertas (`finished_at is None`) |
| `list_done()` | Só as finalizadas |

O estado aberto/finalizado não é um campo à parte: é o próprio `finished_at`,
que vale `None` enquanto a tarefa está aberta. Isso tem uma consequência direta
no protocolo — **`None` não é serializável em XML-RPC por padrão**, porque
`<nil>` é uma extensão. Daí o `allow_none=True` nas duas pontas:

```python
SimpleXMLRPCServer((HOST, PORT), allow_none=True)
xmlrpc.client.ServerProxy(url, allow_none=True, use_datetime=True)
```

As datas viajam como `<dateTime.iso8601>` — o marshaller converte `datetime` do
Python automaticamente —, e o `use_datetime=True` faz o cliente reconstruir
`datetime` no lugar do `xmlrpc.client.DateTime` que viria por padrão.

**Validações** recusadas com `Fault`, cada uma com seu código, mantendo o
servidor no ar:

| Código | Situação |
|---|---|
| `100` / `101` | Título vazio / descrição que não é string |
| `102` | Descrição acima de **500 caracteres** |
| `404` | `finish_task` de um id inexistente |
| `409` | `finish_task` de uma tarefa já finalizada |

**Cliente.** Percorre o roteiro do roteiro — cria 3 tarefas, lista todas,
finaliza uma, lista finalizadas, lista abertas — e transforma cada etapa em uma
verificação:

```
validação:
  [OK] as 3 tarefas criadas aparecem em list_all
  [OK] a tarefa finalizada aparece em list_done
  [OK] a tarefa finalizada sumiu de list_open
  [OK] as outras 2 continuam abertas
  [OK] list_all == list_open + list_done
  [OK] toda tarefa tem id, título, criação, término e descrição
  [OK] descrição acima de 500 caracteres -> Fault 102: a descrição excede 500 caracteres (recebidos: 501)
  [OK] finalizar tarefa inexistente -> Fault 404: tarefa #999999 não encontrada
  [OK] finalizar tarefa já finalizada -> Fault 409: tarefa #2 já foi finalizada

resultado: interface validada
```

> As checagens são feitas sobre os **ids criados na execução**, e não sobre
> contagens absolutas: como o servidor guarda o estado em memória, rodar o
> cliente várias vezes contra o mesmo servidor acumula tarefas e ainda assim a
> validação passa.

### Como executar

O `tcp_echo.py` roda em dois terminais — o primeiro como servidor, o segundo como
cliente:

```bash
cd 02-sockets

# terminal 1 (servidor)
python tcp_echo.py -s --serial -b 1   # sem threads, listen(1)
python tcp_echo.py -s --serial -b 2   # sem threads, listen(2)
python tcp_echo.py -s -b 1            # com threads (padrão)

# terminal 2 (cliente)
python tcp_echo.py                    # uma requisição
python tcp_echo.py -n 2               # duas requisições simultâneas
python tcp_echo.py -n 4               # estoura a fila do listen(1)
```

O `http_get.py` sobe o servidor HTTP; o cliente pode ser o navegador, o `curl` ou
qualquer socket:

```bash
# terminal 1
python http_get.py

# terminal 2
curl -v http://localhost:50007/     # ou abra a URL no navegador
```

O `xmlrpc_math.py` volta ao par servidor/cliente do primeiro etapa:

```bash
# terminal 1
python xmlrpc_math.py -s

# terminal 2
python xmlrpc_math.py
```

O `task_service` separa servidor e cliente em arquivos próprios:

```bash
# terminal 1
python task_service_server.py

# terminal 2
python task_service_client.py
```

> Todos os scripts usam a **mesma porta 50007**: encerre um servidor antes de
> subir outro, ou o `bind()` falha com `OSError: [Errno 98] Address already in
> use`.

## Licença

Distribuído sob os termos do arquivo [LICENSE](LICENSE).

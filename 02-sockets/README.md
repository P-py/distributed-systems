# 02 — Sockets, HTTP e XML-RPC

Este módulo explora a comunicação entre processos usando a **API de redes
(sockets)**: o comportamento da **fila de espera** do `listen()` e, subindo de
nível, o **HTTP** construído sobre esses sockets e o **XML-RPC** construído
sobre o HTTP.

## Contexto

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

## Estrutura

```
02-sockets/
├── tcp_echo.py               # Echo server TCP: backlog do listen() e threads
├── http_get.py               # Servidor HTTP: tratando uma requisição GET
├── xmlrpc_math.py            # XML-RPC: expondo funções sobre o HTTP
├── task_service_server.py    # Lista de tarefas: serviço XML-RPC
└── task_service_client.py    # Lista de tarefas: validação da interface
```

## Os scripts

### `tcp_echo.py` — fila de espera e atendimento concorrente

O script estende o par cliente/servidor mínimo com o que é preciso para
observar a fila:

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

### `http_get.py` — HTTP: tratando uma requisição GET

O **HTTP** nasceu para o transporte de arquivos — inicialmente o HTML e os
demais recursos que compunham uma página. Na prática, é uma forma **básica de
RPC** (chamada de procedimento remoto): implementa alguns comandos, ou
**verbos** (`GET`, `HEAD`, `POST`, `PUT` etc.), e cada um deles tem um **padrão
de texto (e bytes)** que descreve a mensagem enviada ao servidor, a qual
desencadeia um processamento e gera uma mensagem de resposta.

A biblioteca padrão do Python já traz esse protocolo pronto sobre os sockets do
script anterior, em `http.server`:

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

### `xmlrpc_math.py` — XML-RPC: expondo funções sobre o HTTP

O **XML-RPC** foi uma forma simplificada de usar a **infraestrutura do HTTP**
para **expor funções** de uma aplicação ao acesso de processos externos. Se o
HTTP já é um RPC básico com verbos fixos, o XML-RPC usa esse transporte para
carregar a chamada de verdade: um `POST` cujo corpo é um XML com o **nome do
método** e seus **parâmetros**, e cuja resposta é o **valor de retorno** — tudo
sobre a mesma porta e o mesmo protocolo do script anterior.

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

### `task_service_server.py` / `task_service_client.py` — lista de tarefas

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

**Cliente.** Percorre o roteiro completo — cria 3 tarefas, lista todas,
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

## Como executar

O `tcp_echo.py` roda em dois terminais — o primeiro como servidor, o segundo
como cliente:

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

O `http_get.py` sobe o servidor HTTP; o cliente pode ser o navegador, o `curl`
ou qualquer socket:

```bash
# terminal 1
python http_get.py

# terminal 2
curl -v http://localhost:50007/     # ou abra a URL no navegador
```

O `xmlrpc_math.py` volta ao par servidor/cliente do primeiro script:

```bash
# terminal 1
python xmlrpc_math.py -s

# terminal 2
python xmlrpc_math.py
```

O serviço de tarefas separa servidor e cliente em arquivos próprios:

```bash
# terminal 1
python task_service_server.py

# terminal 2
python task_service_client.py
```

> Todos os scripts usam a **mesma porta 50007**: encerre um servidor antes de
> subir outro, ou o `bind()` falha com `OSError: [Errno 98] Address already in
> use`.

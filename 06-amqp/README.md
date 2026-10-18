# 06 — Mensageria com AMQP

Este módulo trata de **mensageria com *broker***: em vez de os processos falarem
direto um com o outro, como no ZeroMQ, todos se conectam a um servidor central
que recebe, guarda e roteia as mensagens. O protocolo é o **AMQP 0-9-1**, e o
*broker* é o [LavinMQ](https://lavinmq.com/), compatível com os clientes do
RabbitMQ.

## Contexto

O [módulo 05](../05-zmq/README.md) mostrou o custo de não ter intermediário: o
`PUB` descarta o que sai antes de o assinante conectar, e o `PUSH` só reparte o
trabalho entre quem já chegou. Com um *broker* no meio, a mensagem fica numa
**fila** até alguém consumi-la, e quem produz não precisa saber quem — nem
quantos — vai consumir.

No AMQP, o produtor publica numa ***exchange***, que decide para quais filas a
mensagem vai segundo os ***bindings*** (ligações entre a *exchange* e cada fila,
com uma chave de roteamento). O consumidor lê da fila e confirma o
processamento com um ***ack*** — aqui sempre com `auto_ack=True`, em que a
própria entrega já conta como confirmação e a mensagem sai da fila na hora.

Quem decide o destino é o **tipo** da *exchange*, comparando a `routing_key` da
mensagem com a `binding_key` de cada ligação:

| Tipo | Entrega para | Onde |
|---|---|---|
| **padrão** (`''`, um `direct`) | a fila cujo nome é a `routing_key` — toda fila já nasce ligada a ela | `exp8_1.py` |
| **direct** | as filas cuja `binding_key` é igual à `routing_key` | `exp8_5.py` (`Greetings`) |
| **fanout** | todas as filas ligadas, ignorando a chave | `exp8_5.py` (`ToAll`) |
| **topic** | as filas cujo padrão casa com a chave, palavra a palavra | `q6/` (`Notifier`) |

## Estrutura

```
06-amqp/
├── docker-compose.yaml   # Sobe o LavinMQ (AMQP, MQTT e gerenciamento)
├── exp8_1.py             # Exchange padrão: --prod publica em greetings/greeter, sem ele consome greetings
├── exp8_5.py             # Exchanges direct (Greetings) e fanout (ToAll) para Fila1 e Fila2
└── q6/                   # Exchange topic com quatro filas filtradas
    ├── broker.py         #   Conexão e consumidor genérico, comuns aos outros scripts
    ├── produtor.py       #   Declara exchange, filas e bindings; publica as 6 chaves embaralhadas
    ├── marketing.py      #   Fila marketing: notification.marketing.message
    ├── support.py        #   Fila support_new: notification.support.new_member
    ├── messages.py       #   Fila messages: notification.*.message
    └── notifications.py  #   Fila notifications: notification.#
```

Os nomes seguem os enunciados (`exp8_<questão>`, e a pasta `q6/` que a questão 6
pede). O `exp8_1.py` e o `exp8_5.py` reproduzem o código dado no enunciado com
as mensagens dele, em inglês e com o `#` antes do corpo, como o `exp6-1.py` do
[módulo 05](../05-zmq/README.md); o `q6/` não traz código no enunciado e segue o
português do resto do repositório.

O `docker-compose.yaml` é o fornecido pelo enunciado, com uma correção: no
original, o bloco `volumes:` de nível superior estava indentado dentro de
`services:`, e o Compose o lia como um serviço chamado `volumes`, recusando o
arquivo:

```
services.volumes additional properties 'lavinmq' not allowed
```

Recuado para o nível de `services:`, ele declara o volume nomeado `lavinmq` que
o serviço monta. O resto ficou como veio.

## Como executar

O LavinMQ roda num contêiner, então é preciso ter o Docker com o Compose (no
WSL, com a integração do Docker Desktop habilitada para a distribuição):

```bash
cd 06-amqp
docker compose up -d        # sobe o broker em segundo plano
docker compose ps           # STATUS: healthy quando estiver pronto
docker compose logs -f      # acompanha o log
docker compose down         # para e remove o contêiner (as filas ficam no volume)
docker compose down -v      # remove também o volume com os dados
```

O *healthcheck* já vem na imagem (`lavinmqctl status`). A imagem é a
`cloudamqp/lavinmq:latest`, como no enunciado: um `docker compose pull` pode
trazer uma versão nova do LavinMQ entre uma execução e outra.

O cliente Python é o `pika`, num `.venv` próprio do módulo (gitignored):

```bash
cd 06-amqp
python3 -m venv .venv
.venv/bin/pip install pika
```

Como no módulo 05, o `argparse` que o enunciado manda instalar já vem na
biblioteca padrão. As saídas abaixo foram medidas com o LavinMQ 2.10.2 e o
`pika` 1.4.4.

Com o *broker* no ar, cada exercício tem um produtor e um ou mais consumidores,
cada um no seu terminal e **em qualquer ordem** (ver
[Observações](#observações)):

```bash
.venv/bin/python exp8_1.py --prod   # terminal 1: publica 2 em greetings e 1 em greeter
.venv/bin/python exp8_1.py          # terminal 2: consome greetings
```

```
Channel over a connection created
Message sent to greetings#Hello!
Message sent to greetings#Good morning!
Message sent to greeter#Greetings!
Connection closed
```

```
Channel over a connection created

Waiting for messages. To exit press CTRL+C 

Received #b'Hello!'
Received #b'Good morning!'
```

```bash
.venv/bin/python exp8_5.py --prod   # terminal 1: uma mensagem por chave
.venv/bin/python exp8_5.py          # terminal 2: consome Fila1 e Fila2
```

```
Message sent to exchangeGreetings#Hello My Friend!
Message sent to exchangeGreetings#Hello Friendo
Message sent to exchangeToAll#Hello Everyone!
```

```
Received on Fila1#b'Hello My Friend!'
Received on Fila1#b'Hello Everyone!'
Received on Fila2#b'Hello Everyone!'
```

O `q6/` tem um consumidor por fila; o produtor publica cada uma das 6 chaves
uma vez por rodada, em ordem aleatória (`-r N` faz N rodadas):

```bash
cd q6
../.venv/bin/python produtor.py -r 2      # terminal 1
../.venv/bin/python marketing.py          # terminais 2 a 5: um por fila
../.venv/bin/python support.py
../.venv/bin/python messages.py
../.venv/bin/python notifications.py
```

```
[marketing] notification.marketing.message: mensagem 6
[marketing] notification.marketing.message: mensagem 8
[support_new] notification.support.new_member: mensagem 4
[support_new] notification.support.new_member: mensagem 10
[messages] notification.support.message: mensagem 2
[messages] notification.marketing.message: mensagem 6
[messages] notification.support.message: mensagem 7
[messages] notification.marketing.message: mensagem 8
[notifications] notification.support.new_ticket: mensagem 1
…                                          ← as 12, na ordem em que saíram
```

O estado do *broker* — filas, mensagens paradas, *exchanges* — aparece na
interface de gerenciamento ou pelo `lavinmqctl` dentro do contêiner:

```bash
docker compose exec lavinmq lavinmqctl list_queues
docker compose exec lavinmq lavinmqctl list_exchanges
```

**As portas** ficam fora das dos módulos 02 (50007), 04 (50051) e 05
(5557–5561):

| Porta | Uso |
|---|---|
| 1883 | MQTT 3.1.0 e 3.1.1 — cada sessão MQTT é uma fila AMQP por baixo |
| 5672 | AMQP — onde os clientes conectam (`amqp://guest:guest@localhost:5672/`) |
| 15672 | Interface de gerenciamento — <http://localhost:15672> |

Diferente do resto do repositório, que faz *bind* só em `localhost`, o arquivo
do enunciado publica as três portas **em todas as interfaces** (`"5672:5672"`
equivale a `0.0.0.0:5672`): o *broker* fica acessível a outras máquinas da rede
— com o usuário padrão. Para restringir ao próprio computador, basta prefixar
cada porta com `127.0.0.1:` (`"127.0.0.1:5672:5672"`).

O usuário padrão é `guest`/`guest`; o LavinMQ restringe esse usuário a conexões
de *loopback*, mas a imagem do Docker sobe com
`--default-user-only-loopback=false`, já que, vista de dentro do contêiner, a
conexão que chega do host não é *loopback*.

O `network_mode: bridge` liga o contêiner à rede `bridge` padrão do Docker, em
vez da rede que o Compose criaria para o projeto; com um serviço só, não muda
nada para quem conecta pelo host.

Os dados (filas, mensagens persistentes, usuários) ficam no volume nomeado
`lavinmq` (`06-amqp_lavinmq` no Docker), montado em `/var/lib/lavinmq`, e
sobrevivem a um `docker compose down`.

## Observações

### A fila fica no *broker*, e a ordem de subida não importa

No `q6/`, o produtor rodou com três dos consumidores ainda parados: as
mensagens esperaram nas filas (`marketing` 2, `support_new` 2, `messages` 4), e
cada consumidor recebeu as suas ao subir. Na ordem inversa, o consumidor fica no
`start_consuming()` e recebe cada mensagem assim que ela é publicada. É o
contrário do `PUB`/`SUB` do [módulo 05](../05-zmq/README.md), que descarta o que
sai antes de o assinante chegar.

Isso só vale porque **os dois lados declaram as filas**: o `queue_declare` cria a
fila se ela não existir e não faz nada se já existir, então quem sobe primeiro a
cria. Pela *exchange* padrão, uma mensagem publicada para uma fila que ainda não
existe é descartada: publicando antes do `queue_declare`, a fila nasceu com 0
mensagens.

A fila também não depende de ninguém consumi-la: ninguém lê a `greeter` do
`exp8_1.py`, e depois de três execuções do produtor o `lavinmqctl list_queues`
mostrava 3 mensagens paradas nela. Filas e *exchanges* continuam declaradas no
*broker* depois que os programas terminam.

O outro lado disso: **um consumidor esquecido aberto leva as mensagens**. Com
consumidores de um teste anterior ainda conectados em outros terminais, uma
nova rodada do `q6/` foi toda para eles, e os consumidores recém-abertos não
receberam nada — o *broker* entrega a quem já está inscrito na fila, e com
`auto_ack=True` a mensagem sai da fila no ato.

### direct e fanout: a mensagem que não casa com nenhum binding some

No `exp8_5.py`, a `Fila1` está ligada a duas *exchanges* ao mesmo tempo: à
`Greetings` pela chave `greeting` e à `ToAll`. Das três mensagens:

| Publicação | Chave | Chega em |
|---|---|---|
| `Greetings` ← `Hello My Friend!` | `greeting` | `Fila1` |
| `Greetings` ← `Hello Friendo` | `helo` | nenhuma |
| `ToAll` ← `Hello Everyone!` | `''` | `Fila1` e `Fila2` |

A *exchange* `direct` não tem *binding* para `helo`, e o *broker* descarta a
mensagem em silêncio: o produtor imprime `Message sent` do mesmo jeito, e o
consumidor só vê três linhas. A `fanout` ignora a chave e copia a mensagem para
cada fila ligada — a cópia por fila é o que a diferencia do `PUSH` do módulo 05,
que entrega cada mensagem a um só.

### topic: direct e tópico numa *exchange* só

O enunciado do `q6/` pede *bindings* "do tipo direto e tópico" numa *exchange*,
mas o tipo é da *exchange*, não do *binding*. A solução é uma *exchange*
`topic` (`Notifier`): uma `binding_key` sem curinga só casa com a chave idêntica,
que é exatamente o comportamento de uma `direct`. A chave é dividida em palavras
pelo `.`, e `*` casa com exatamente uma palavra, `#` com zero ou mais:

| Fila | `binding_key` | Por rodada | Medido com `-r 2` |
|---|---|---|---|
| `marketing` | `notification.marketing.message` | 1 | 2 |
| `support_new` | `notification.support.new_member` | 1 | 2 |
| `messages` | `notification.*.message` | 2 (`marketing` e `support`) | 4 |
| `notifications` | `notification.#` | 6 | 12 |

A mesma mensagem chega a várias filas: `notification.marketing.message` foi para
`marketing`, `messages` e `notifications`.

O produtor embaralha a lista de chaves (`random.sample`) em vez de sortear com
reposição: a ordem é aleatória, mas toda chave sai uma vez por rodada, e todo
filtro é exercitado. Sorteando 6 chaves ao acaso, a chance de faltar ao menos
uma passa de 98%.

### O corpo é bytes, e o CTRL+C não é Exception

O `pika` entrega o corpo como `bytes`. O `exp8_1.py` e o `exp8_5.py` imprimem o
`body` como o enunciado escreveu, por isso aparece `b'Hello!'`; o `q6/` faz
`body.decode()`.

O `except Exception` do enunciado não pega o CTRL+C: `KeyboardInterrupt` herda
de `BaseException`, não de `Exception`. No `exp8_1.py` e no `exp8_5.py`, o
CTRL+C encerra o consumidor com o *traceback* do `KeyboardInterrupt` saindo de
dentro do `start_consuming()`, e o `sys.exit(0)`/`os._exit(0)` do enunciado
nunca roda. O consumidor do `q6/` (`broker.py`) captura o `KeyboardInterrupt`,
imprime `Encerrando` e fecha a conexão.

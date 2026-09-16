# 01 — Memória Compartilhada

Este módulo explora a **comunicação entre processos (IPC)** usando
**memória compartilhada** (`shared_memory`), sincronização com **semáforos** e
gerenciadores de alto nível (`Manager` / `SharedMemoryManager`).

## Contexto

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

## Estrutura

```
01-shared-memory/
├── shm_semaphore.py              # SHM + Semáforo (leitura/escrita, medição de tempo)
├── shm_numpy_histogram.py        # SHM + NumPy (cálculo de histograma)
└── manager_producer_consumer.py  # Managers (produtor/consumidor com Value/Event)
```

## Os scripts

### `shm_semaphore.py` — SHM e Semáforo: medindo o tempo de acesso

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
- Ao final imprime os **tempos médios** de aquisição e de operação, em
  notação científica (`{:.2e}`).
- O supervisor aguarda os filhos com `os.waitpid` e sempre libera a SHM com
  `.close()` **e** `.unlink()`.

> Observação: aumentando o tamanho do bloco, os tempos ficam na casa dos
> microssegundos. Valores maiores que o tamanho de uma página (~4 KB) começam a
> impactar mais o tempo de execução.

### `shm_numpy_histogram.py` — SHM e NumPy: cálculo de histograma

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

### `manager_producer_consumer.py` — Managers: produtor/consumidor

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

## Como executar

```bash
# com o .venv ativo e o NumPy instalado
cd 01-shared-memory
python shm_semaphore.py
python shm_numpy_histogram.py
python manager_producer_consumer.py
```

> **Plataforma:** os exemplos dependem de `os.fork()` e da semântica de SHM do
> POSIX; execute em **Linux/Unix** (ou WSL no Windows).

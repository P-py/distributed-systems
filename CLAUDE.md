# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal lab on inter-process communication and distributed programming:
three self-contained modules that walk through IPC mechanisms in increasing
order of reach — shared memory (one machine) → sockets/HTTP/XML-RPC (across
machines) → serialization (what travels over the channel). There is no build
system, no package manifest, no test framework: each module is a handful of
standalone scripts plus a README that explains what they demonstrate.

```
01-shared-memory/     shm + semaphores, NumPy views, Manager/producer-consumer
02-sockets/           TCP echo, HTTP GET, XML-RPC, XML-RPC task service + client
03-serialization/     native/ (ObjectOutputStream, pickle), json/ (Gson), protobuf/
```

Each module's `README.md` is where the real analysis lives (measured timings,
byte counts, failure modes); it is usually far more informative than the code
itself. Keep it in sync when behavior changes — the numbers in it are measured,
not estimated, so re-measure rather than adjusting them by hand.

## Language and commit conventions

- **All prose, comments, and program output are Brazilian Portuguese.** New
  docs, comments, and printed messages must be written in pt-BR to match.
- Identifiers and CLI flags stay in English.
- Commit messages are gitmoji + conventional type, e.g.
  `:rocket: feat: add XML-RPC service`, `:memo: docs: ...`, `:wrench: ops: ...`.

## Keeping the repo clean of personal data

This repo is public. Sample data only — never commit a real name, id number, or
anything personal, and note that **base64 is not encryption**: the streams in
`03-serialization` carry every field in cleartext, so a real object must be
passed as a CLI argument, never pasted into a constant or a README. The
`BASE64` constants in `native/` exist as samples (`Alan Turing`) and the
programs accept the string as `argv[1]` precisely so nothing real gets
versioned.

## Running things

Target runtime is **Python 3.8** (`python3` here is 3.8.10), which is why the
serialization scripts start with `from __future__ import annotations` —
`list[int]` annotations would otherwise fail. Don't introduce 3.9+ syntax.

`01-shared-memory/` and `02-sockets/` each carry their own gitignored `.venv`;
only `shm_numpy_histogram.py` needs a third-party package (NumPy).

```bash
cd 01-shared-memory && python shm_semaphore.py   # needs POSIX fork()/SHM
cd 02-sockets && python tcp_echo.py -s           # server; client in a 2nd terminal
cd 02-sockets && python tcp_echo.py -n 4         # client(s)
```

**Every 02-sockets script binds port 50007** — one server at a time, or `bind()`
fails with `EADDRINUSE`. Most are a single file with `-s/--server` selecting the
role; the task service is split into `task_service_server.py` / `_client.py`.

**Native serialization (03-serialization/native)** must be compiled as a set —
the single-file source launcher does not work, since `Serializer` and
`Deserializer` depend on `Person`:

```bash
javac -d java/out java/*.java && java -cp java/out Serializer
java -cp java/out Deserializer "$(java -cp java/out Serializer | sed 's/^Base64: //')"
python3 deserialize.py "$(python3 serialize.py)"
```

The chained forms are the closest thing to a test suite: both deserializers
re-serialize the recovered object and compare it with the input, so a mismatch
is reported explicitly and the exit status is non-zero.

## The json/ and protobuf/ runners

Each has a `run.sh` plus a `run.bat` that mirrors it for Windows — keep the two
in sync when either changes.

- `json/run.sh` downloads `gson-2.13.1.jar` if missing (jars are gitignored),
  compiles, and runs all four Java↔Python exchange cases. The classpath needs
  **both** `java/` and the jar: `-cp "java:java/gson-2.13.1.jar"`.
- `protobuf/run.sh` runs `protoc --java_out=java` and `--python_out=python`
  separately. The generated sources *are* committed so the repo builds without
  `protoc`; regenerate them when `MyApp.proto` changes rather than hand-editing.
  `protoc --encode=Person` / `--decode=Person` inspect the wire format without
  any runtime library.

## Cross-module facts

- The `Person` object is the same across all of `03-serialization` — `name`
  (string), `enrollNumber` (int), `height` (float), `luckNumbers` (list of int)
  — so the formats can be compared over identical data. Java uses camelCase
  fields and bridges to the Python `Name`/`EnrollNumber`/… naming via Gson's
  `UPPER_CAMEL_CASE` policy; the shared field list is duplicated as the `CAMPOS`
  constant on both sides.
- `native/deserialize.py` redefines `Person` instead of importing it from
  `serialize.py` on purpose: pickle records the defining module (`__main__`),
  so importing the class would change the recorded path and break the
  round-trip check. Don't "clean this up".

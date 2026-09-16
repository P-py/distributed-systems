# 03 — Serialização

Este módulo trata da **serialização**: transformar os objetos de uma linguagem
em dados sequenciais para transporte ou armazenamento (persistência). O mesmo
objeto `Person` atravessa três formatos — os **nativos** de cada linguagem, o
**JSON** e o **Protocol Buffers** — e a comparação entre eles é o assunto.

## Contexto

O formato serializado pode ser **proprietário e fixo da própria linguagem**: só
volta a ser objeto no mesmo ambiente (mesma linguagem, mesma versão) — é o caso
do `pickle` e da serialização nativa do Java. Ou pode ser **aberto e neutro**,
permitindo recuperar o objeto em outro ambiente (linguagem/versão diferentes) —
é o caso do JSON e do Protocol Buffers.

Os pontos negativos de um formato em linguagem neutra:

- **Ineficiente** — muitos formatos neutros adotam texto (strings), que gasta
  mais bytes para alguns tipos de dados.
- **Limitado ou ambíguo** — o JSON restringe os tipos suportados; o XML admite
  mais de uma forma de representar o mesmo dado
  (`<value><int>12</int></value>` ou `<value type="int">12</value>`).

O Protocol Buffers é a resposta a esses dois pontos: binário como os formatos
nativos, neutro como o JSON, e com o esquema declarado numa **IDL** compilada
para as duas linguagens.

## Estrutura

```
03-serialization/
├── native/                 # Formatos nativos: ida e volta em cada linguagem
│   ├── serialize.py        #   pickle → base64
│   ├── deserialize.py      #   base64 → objeto, validando a integridade
│   └── java/
│       ├── Serializer.java     # ObjectOutputStream → base64
│       ├── Deserializer.java   # base64 → objeto, validando a integridade
│       └── Person.java         # O objeto serializado (implements Serializable)
├── json/                   # Formato neutro: Java e Python trocando o objeto
│   ├── run.sh / run.bat    #   Compila e roda a troca nos dois sentidos
│   ├── java/
│   │   ├── MyApp.java      #   Envia e recebe JSON via Gson
│   │   └── Person.java     #   A mesma classe do native/, reaproveitada
│   └── python/MyApp.py     #   A outra ponta, com o json da biblioteca padrão
└── protobuf/               # Formato binário neutro, a partir de uma IDL
    ├── MyApp.proto         #   O Person escrito na IDL do proto3
    ├── run.sh / run.bat    #   Chama o protoc para as duas linguagens
    ├── java/               #   Código gerado pelo protoc (versionado)
    └── python/             #   Código gerado pelo protoc (versionado)
```

Nos três formatos o objeto `Person` tem os mesmos quatro campos — `name`
(string), `enrollNumber` (int), `height` (float) e `luckNumbers` (lista de
inteiros) — para que possam ser comparados sobre o mesmo dado.

> **Os dados são de amostra, e o base64 não é criptografia.** A string base64 do
> stream **contém todos os campos em claro**: qualquer um decodifica e lê. Por
> isso as constantes `BASE64` guardam um stream de exemplo (`Alan Turing`), e
> qualquer dado real deve ser passado **por argumento** na linha de comando, sem
> ser gravado no código nem no README.

As duas pontas da volta aceitam o base64 **por argumento** e, sem argumento,
usam a constante de amostra. A constante sozinha é uma fotografia: se os dados
do serializador mudarem, ela continua descrevendo o objeto antigo sem reclamar
— daí a validação por re-serialização descrita abaixo.

## Como executar

### Formatos nativos

O *single-file source launcher* (`java Serializer.java`) **não** serve aqui: ele
só compila programas de múltiplos arquivos a partir do Java 22, e o
`Serializer` depende de `Person`. Compile os três juntos:

```bash
cd 03-serialization/native
javac -d java/out java/*.java
java -cp java/out Serializer
```

Saída:

```
Base64: rO0ABXNyAAZQZXJzb27XA7FpGjZTSgIABEkADGVucm9sbE51bWJlckYABmhlaWdodEwAC2x1Y2tOdW1iZXJzdAAQTGphdmEvdXRpbC9MaXN0O0wABG5hbWV0ABJMamF2YS9sYW5nL1N0cmluZzt4cAAGeTI/4o9cc3IAE2phdmEudXRpbC5BcnJheUxpc3R4gdIdmcdhnQMAAUkABHNpemV4cAAAAAN3BAAAAANzcgARamF2YS5sYW5nLkludGVnZXIS4qCk94GHOAIAAUkABXZhbHVleHIAEGphdmEubGFuZy5OdW1iZXKGrJUdC5TgiwIAAHhwAAAAB3NxAH4ABgAAABdzcQB+AAYAAAAveHQAC0FsYW4gVHVyaW5n
```

O lado Python faz o mesmo caminho com o `pickle`:

```bash
python3 serialize.py
```

```
gASVcgAAAAAAAACMCF9fbWFpbl9flIwGUGVyc29ulJOUKYGUfZQojAROYW1llIwLQWxhbiBUdXJpbmeUjAxFbnJvbGxOdW1iZXKUSjJ5BgCMBkhlaWdodJRHP/xR64UeuFKMC0x1Y2tOdW1iZXJzlF2UKEsHSxdLL2V1Yi4=
```

A volta roda com a constante de amostra ou com a string passada por argumento —
esta segunda forma encadeia as duas metades e valida o objeto gerado agora:

```bash
java -cp java/out Deserializer
python3 deserialize.py

java -cp java/out Deserializer "$(java -cp java/out Serializer | sed 's/^Base64: //')"
python3 deserialize.py "$(python3 serialize.py)"
```

Saída:

```
Name: Alan Turing
EnrollNumber: 424242
Height: 1.77
LuckNumbers: [7, 23, 47]
OK: objeto recuperado integralmente (re-serialização idêntica)
```

### JSON

As duas aplicações são simétricas: **sem argumento** criam o seu objeto,
serializam para JSON e imprimem numa linha; **com argumento** leem o JSON
recebido e imprimem uma propriedade por linha. A saída de uma serve de entrada
para a outra, nos dois sentidos.

```bash
cd 03-serialization/json
./run.sh              # baixa o Gson se faltar, compila e roda os 4 casos
```

Ou um de cada vez — note o classpath, que precisa do diretório das classes
**e** do jar do Gson:

```bash
javac -cp java/gson-2.13.1.jar -d java java/*.java

java -cp "java:java/gson-2.13.1.jar" MyApp                    # 1: Java gera
python3 python/MyApp.py                                       # 2: Python gera
python3 python/MyApp.py "$(java -cp "java:java/gson-2.13.1.jar" MyApp)"   # 3: Java → Python
java -cp "java:java/gson-2.13.1.jar" MyApp "$(python3 python/MyApp.py)"   # 4: Python → Java
```

Saída dos quatro:

```
{"Name":"Ada Lovelace","EnrollNumber":100001,"Height":1.68,"LuckNumbers":[2,11,29]}
{"Name":"Grace Hopper","EnrollNumber":200002,"Height":1.6,"LuckNumbers":[5,13,41]}

Name: Ada Lovelace          Name: Grace Hopper
EnrollNumber: 100001        EnrollNumber: 200002
Height: 1.68                Height: 1.60
LuckNumbers: [2, 11, 29]    LuckNumbers: [5, 13, 41]
```

O Gson não é versionado (é binário de terceiro): o `run.sh` baixa na primeira
execução, e o `.gitignore` cobre `*.jar`.

### Protocol Buffers

O código das duas linguagens é **gerado** a partir da IDL pelo compilador
`protoc`; o `run.sh` refaz a geração:

```bash
cd 03-serialization/protobuf
./run.sh
```

```
=== 1/2: gerar o código Java ===
protoc --java_out=java MyApp.proto
MyAppProto.java
Person.java
PersonOrBuilder.java

=== 2/2: gerar o código Python ===
protoc --python_out=python MyApp.proto
MyApp_pb2.py
```

O próprio `protoc` também serializa e desserializa da linha de comando, o que
permite ver o formato sem escrever nenhum código:

```bash
printf 'name: "Alan Turing"\nenroll_number: 424242\nheight: 1.77\nluck_numbers: 7\nluck_numbers: 23\nluck_numbers: 47\n' \
  | protoc --encode=Person MyApp.proto | xxd
```

## Observações

### Os formatos nativos (Java e pickle)

**A serialização do Java carrega o esquema junto; o pickle não.** Com os mesmos
dados de amostra, o Java produz **285 bytes** contra **125 bytes** do pickle —
mais que o dobro. A diferença não está nos valores, e sim no que cada formato
grava em volta deles. Dá para ler o stream do Java quase inteiro em ASCII:

```
Person ... enrollNumber F height L luckNumbers t Ljava/util/List;
L name t Ljava/lang/String; ... java.util.ArrayList ... java.lang.Integer
... java.lang.Number
```

Ou seja: o nome da classe, o **nome e o tipo de cada campo**, e ainda a
descrição completa de `ArrayList`, `Integer` e da superclasse `Number` — cada
classe com seu `serialVersionUID`. O leitor consegue validar a compatibilidade
do que recebeu antes de reconstruir o objeto.

O pickle grava só `__main__` + `Person` e os valores (`pickletools.dis` mostra
o bytecode da máquina de pilha do formato):

```
SHORT_BINUNICODE '__main__' / 'Person' / STACK_GLOBAL / NEWOBJ
'Name' / 'Alan Turing' / 'EnrollNumber' / BININT 424242 / ...
```

Os nomes dos campos aparecem porque são as chaves do `__dict__` do objeto, não
porque o formato descreva tipos. Nenhuma informação de tipo é gravada: o
`BININT` diz como ler os bytes, não que o campo seja um `int`. A classe precisa
existir do outro lado — e é o próprio pickle que a **importa** ao desserializar,
o que torna `pickle.loads` de dado não confiável uma forma de executar código
arbitrário.

**Ambos são nativos, mas por motivos diferentes.** O stream do Java é
autodescritivo o bastante para outra linguagem interpretar, mas está amarrado
ao `serialVersionUID` de cada classe e à semântica de objetos da JVM. O pickle
é um bytecode de uma máquina de pilha do CPython, e sequer é estável entre
protocolos — `pickle.DEFAULT_PROTOCOL` mudou de versão para versão do Python
(aqui, protocolo 4, do Python 3.8).

### O que quebra na volta

**Validar "integralmente" no Java não pode passar por `equals()`.** `Person` não
implementa `equals()`, então comparar o objeto recuperado com o original cairia
no `Object.equals` — identidade de referência, sempre `false`. E acrescentar um
`equals()` à classe é pior: o `serialVersionUID` **padrão** é calculado a partir
do nome da classe, dos campos *e das assinaturas dos métodos*, de modo que o
simples ato de adicionar o método muda o UID e invalida todo stream gerado
antes:

```
$ serialver Person        # sem equals()
Person: private static final long serialVersionUID = -2953321865655463094L;
$ serialver Person        # com equals()
Person: private static final long serialVersionUID = 2707297536030986793L;
```

Por isso o `Deserializer` valida **re-serializando** o objeto recuperado e
comparando o base64 com o de entrada: é a prova de que nada se perdeu, não
depende de valores fixos no código e não toca no `Person`. (Em código de
produção, a resposta certa é declarar
`private static final long serialVersionUID = 1L;` explicitamente, e aí a classe
pode evoluir sem quebrar os streams antigos — mas declará-lo agora mudaria a
string base64 de amostra.)

No Python o `@dataclass` gera `__eq__` de graça, então `p == Person(...)`
funcionaria; o script usa a mesma comparação por re-serialização para não
duplicar os dados nos dois arquivos.

**Um `catch` genérico esconde o diagnóstico.** Os três casos abaixo cairiam
todos no mesmo `catch (IOException ex)` com uma mensagem fixa, que não diz nada.
Imprimindo a exceção real, cada uma nomeia exatamente o problema:

| Situação | Mensagem real |
|---|---|
| `Person` ganhou um campo desde que o stream foi gerado | `InvalidClassException: Person; local class incompatible: stream classdesc serialVersionUID = -2953321865655463094, local class serialVersionUID = -2017023037252057138` |
| O base64 passado é o do pickle, não o do Java | `StreamCorruptedException: invalid stream header: 80049572` |
| A classe `Person` não está no classpath | `ClassNotFoundException: Person` |

**Os dois formatos não se cruzam — é o que "nativo" quer dizer.** O Java recusa
o pickle logo no cabeçalho (`ObjectStreamConstants.STREAM_MAGIC` é `0xACED`, e o
pickle começa com `\x80\x04`); o pickle recusa o stream do Java no primeiro
opcode:

```
$ python3 deserialize.py "$(java -cp java/out Serializer | sed 's/^Base64: //')"
Falha ao desserializar: UnpicklingError: invalid load key, '\xac'.
```

**O pickle amarra o objeto ao módulo em que a classe foi definida.** O stream
grava `__main__` + `Person`, e o `__main__` é resolvido **no momento da leitura**
— não é o módulo original, é o script que estiver rodando. Funciona aqui porque
`deserialize.py` também roda como `__main__` e **redefine** a classe em vez de
importá-la do `serialize.py`. Mova a mesma classe para um módulo importado e o
caminho gravado deixa de bater:

```
AttributeError: Can't get attribute 'Person' on <module '__main__' from 'runner.py'>
```

O Java não tem esse problema — o stream guarda o nome da classe, resolvido pelo
*class loader*.

**`height` não é o mesmo tipo dos dois lados.** O `float` do Java tem 32 bits, o
`float` do Python tem 64 (é o `double` do C). O `1.77f` do Java, lido como
double, é `1.7699999809265137`; o `1.77` do Python é o double mais próximo de
1.77. As saídas parecem iguais só porque o `%.2f` do Java arredonda — mais uma
razão para os dois streams não serem intercambiáveis nem em tese.

**Detalhe de versão no Python.** A anotação `list[int]` só vale a partir do
Python 3.9. Os scripts trazem `from __future__ import annotations`, que adia a
avaliação das anotações e faz o mesmo código rodar no Python 3.8 — versão
instalada neste ambiente (a mesma usada nos módulos 01 e 02).

### O que o JSON resolve, e o que ele passa para você

**Resolve o que os formatos nativos não conseguiam.** Lá, o Java recusava o
pickle no cabeçalho e o pickle recusava o stream do Java no primeiro opcode.
Aqui a mesma string atravessa nos dois sentidos, sem nenhuma biblioteca em comum
entre as duas pontas.

**O formato é neutro; o esquema, não.** Os campos do `Person` do Java são
`name`, `enrollNumber`, `height`, `luckNumbers`; os do *dataclass* do Python são
`Name`, `EnrollNumber`, `Height`, `LuckNumbers`. Nada no JSON reconcilia isso —
serializado direto, cada lado produziria chaves que o outro ignoraria em
silêncio. A ponte é uma linha de configuração do Gson:

```java
new GsonBuilder().setFieldNamingPolicy(FieldNamingPolicy.UPPER_CAMEL_CASE).create()
```

É o contraste exato com o formato nativo: o stream do Java **carregava** os
nomes e os tipos de cada campo, e por isso conseguia recusar um objeto
incompatível. O JSON não carrega nada disso, e a compatibilidade vira um acordo
combinado fora do arquivo — no caso, a constante `CAMPOS`, repetida nos dois
programas.

**Nenhum tipo é verificado, e o erro é silencioso.** Mandando `"Height":"1.7"`
(string, não número), os dois aceitam sem reclamar — e de formas diferentes:

```
Java:   Height: 1.70      ← o Gson converteu a string para float
Python: Height: 1.7       ← continuou str; a anotação `Height: float` não valida nada
```

Pior é o inteiro. O JSON não tem limite de tamanho para números; o `int` do Java
tem 32 bits:

```
{"EnrollNumber":99999999999,...}
Java:   EnrollNumber: 1215752191     ← truncado nos 32 bits baixos, sem erro nenhum
Python: EnrollNumber: 99999999999    ← intacto
```

Nenhuma exceção, nenhum aviso: o dado chega corrompido e o programa segue. É o
tipo de defeito que o formato nativo não deixava acontecer — e o motivo de a
conferência das chaves obrigatórias estar escrita à mão nos dois lados.

### O que o Protocol Buffers acrescenta

**O esquema volta, mas fora do dado.** O `.proto` declara os campos e seus
tipos, e o `protoc` gera a classe `Person` para cada linguagem. As duas pontas
passam a compartilhar a mesma definição sem compartilhar biblioteca de
execução — é o esquema do formato nativo do Java, só que combinado antes e não
transmitido a cada mensagem.

**O que vai no fio são tags, não nomes.** Os mesmos dados de amostra ocupam
**27 bytes**, contra 285 do stream do Java:

```
00000000: 0a0b 416c 616e 2054 7572 696e 6710 b2f2  ..Alan Turing...
00000010: 191d 5c8f e23f 2203 0717 2f              ..\..?".../
```

Cada campo vira um byte de tag (número do campo + tipo no fio) e o valor
codificado: `0a 0b` abre o campo 1 com 11 bytes de string, `10 b2f219` é o
campo 2 como *varint*, `1d` + 4 bytes é o campo 3 como *fixed32*, e `22 03` é o
campo 4 empacotado com os três inteiros. Nenhum nome de campo aparece — é por
isso que **o número do campo na IDL é o contrato**, e renumerar um campo quebra
a compatibilidade de um jeito que renomeá-lo não quebra.

**Duas opções da IDL evitam colisão de nomes no Java:**

```proto
option java_outer_classname = "MyAppProto";  // sem isto a classe externa se chamaria MyApp
option java_multiple_files = true;           // Person em arquivo próprio
```

**O código gerado é versionado de propósito.** Assim o repositório pode ser
lido (e o Java compilado) sem ter o `protoc` instalado; quando o `.proto` muda,
o certo é rodar o `run.sh` de novo, nunca editar o gerado à mão.

### Tamanho: "texto gasta mais bytes" depende do dado

Para o objeto de amostra, o JSON é o **menor** dos formatos textuais e o
Protocol Buffers ganha de todos:

| Formato | Bytes |
|---|---|
| Java nativo | 285 |
| pickle | 125 |
| JSON | 82 |
| Protocol Buffers | 27 |

O stream do Java paga o esquema que carrega, e o pickle paga os opcodes e o
enquadramento. A ineficiência do texto só aparece quando o dado é numérico em
volume — trocando os 3 números da sorte por 1000 inteiros de 9 dígitos, a ordem
se inverte entre JSON e pickle:

| Formato | Bytes (1000 inteiros) |
|---|---|
| JSON | 10.074 |
| pickle | 5.119 |
| Protocol Buffers | 4.843 |

Em registros pequenos com strings curtas, o formato neutro ganha também em
tamanho; em volume numérico, o texto custa mais que o dobro do binário.

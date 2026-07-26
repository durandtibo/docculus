# Document Stores

:book: This page describes the `docculus.store` package, which provides a uniform interface for
persisting [LangChain](https://python.langchain.com/) `Document` objects, backed by
[`persista`](https://pypi.org/project/persista/) key-value stores.

**Prerequisites:** You'll need to know a bit of Python, and the `persista` extra
(`docculus[persista]`) must be installed. For a Python refresher, see the
[Python tutorial](https://docs.python.org/tutorial/).

## Overview

The `docculus.store` package provides:

- `BaseDocumentStore`: a single abstract interface that supports both synchronous methods (`get`,
  `set_many`, ...) and their asynchronous, `a`-prefixed counterparts (`aget`, `aset_many`, ...) on
  the same instance
- `DocumentStore`: the concrete implementation of `BaseDocumentStore`, wrapping any
  `persista.store.BaseStore`
- Ready-to-use `DocumentStore` subclasses backed by specific `persista` backends:
  `InMemoryDocumentStore`, `SQLiteDocumentStore`, `DuckDBDocumentStore`, and their "typed" variants
  `TypedSQLiteDocumentStore`/`TypedDuckDBDocumentStore`

Documents are keyed by their `id`; the `id` itself is not duplicated inside the stored value.
Every store exposes:

- `get`/`aget`, `get_many`/`aget_many`: read one or several documents by `id`
- `set_many`/`aset_many`: add or replace documents (upsert semantics)
- `filter`/`afilter`: retrieve documents whose metadata matches given keyword filters (`AND`-ed
  together)
- `delete`/`adelete`, `delete_many`/`adelete_many`: remove documents by `id`
- `clear`/`aclear`: remove every document
- `contains`/`acontains`, `contains_many`/`acontains_many`: check which IDs exist
- `keys`/`akeys`, `values`/`avalues`, `iter_batches`/`aiter_batches`: iterate over stored documents
- `count`/`acount`: number of documents
- `open`/`aopen`, `close`/`aclose`, `closed`: connection lifecycle

Because every store implements the same `BaseDocumentStore` interface, application code can move
between backends -- for example using `InMemoryDocumentStore` in tests and `SQLiteDocumentStore`
or `DuckDBDocumentStore` in production -- without changes, and can freely mix sync and async calls
on the same store instance.

## Getting Started

### In-Memory Store

`InMemoryDocumentStore` keeps documents in a plain Python `dict` (via `persista.store.InMemoryStore`).
It requires no setup and is a good default for tests and prototyping:

```pycon
>>> from docculus.store import InMemoryDocumentStore
>>> from langchain_core.documents import Document
>>> with InMemoryDocumentStore() as store:  # doctest: +SKIP
...     store.set_many(
...         [Document(id="1", page_content="hello", metadata={"author": "Alice"})]
...     )
...     print(store.count())
...     print(store.get("1"))
...
1
Document(id='1', page_content='hello', metadata={'author': 'Alice'})

```

Constructing a store does not connect to the underlying backend -- every method (other than
`open`/`aopen`) raises `RuntimeError` until the store has been opened, either by calling
`open()`/`aopen()` explicitly or by using it as a context manager, as above. Every store supports
the context manager protocol, which calls `open()` on entry and `close()` automatically on exit --
prefer it over calling `open()`/`close()` manually so the underlying resources are always
released.

### Setting Multiple Documents

`set_many` writes several documents in a single call, upserting any whose `id` already exists.
`filter` retrieves the documents whose metadata matches the given keyword arguments (all filters
are combined with `AND`):

```pycon
>>> from docculus.store import InMemoryDocumentStore
>>> from langchain_core.documents import Document
>>> with InMemoryDocumentStore() as store:  # doctest: +SKIP
...     store.set_many(
...         [
...             Document(
...                 id="1", page_content="Intro to Python", metadata={"author": "Alice"}
...             ),
...             Document(
...                 id="2", page_content="Advanced Python", metadata={"author": "Alice"}
...             ),
...             Document(
...                 id="3", page_content="History of Rome", metadata={"author": "Bob"}
...             ),
...         ]
...     )
...     print(len(store.filter(author="Alice")))
...     print(len(store.filter()))
...
2
3

```

### Deleting and Clearing

```pycon
>>> from docculus.store import InMemoryDocumentStore
>>> from langchain_core.documents import Document
>>> with InMemoryDocumentStore() as store:  # doctest: +SKIP
...     store.set_many(
...         [Document(id="1", page_content="a"), Document(id="2", page_content="b")]
...     )
...     store.delete("1")
...     print(store.count())
...     store.clear()
...     print(store.count())
...
1
0

```

## SQL-Backed Stores

### SQLite

`SQLiteDocumentStore` persists documents in a SQLite database, storing each document's
`page_content` and `metadata` in a single JSON `metadata` column. It works both with a file path
and with `":memory:"`:

```pycon
>>> from docculus.store import SQLiteDocumentStore
>>> from langchain_core.documents import Document
>>> with SQLiteDocumentStore() as store:  # doctest: +SKIP
...     store.set_many(
...         [Document(id="1", page_content="Intro to Python", metadata={"author": "Alice"})]
...     )
...     print(store.get("1"))
...
Document(id='1', page_content='Intro to Python', metadata={'author': 'Alice'})

```

To persist to disk, pass a file path instead of the default `":memory:"`:

```python
from pathlib import Path

from docculus.store import SQLiteDocumentStore

with SQLiteDocumentStore(Path("tmp/data.sqlite")) as store:
    ...
```

### DuckDB

`DuckDBDocumentStore` works the same way as `SQLiteDocumentStore` but is backed by
[DuckDB](https://duckdb.org/) (requires the `duckdb` extra):

```python
from docculus.store import DuckDBDocumentStore

with DuckDBDocumentStore() as store:
    ...
```

### Typed Stores

`TypedSQLiteDocumentStore` and `TypedDuckDBDocumentStore` map selected metadata fields onto native
SQL columns, via a `metadata_schema` that maps metadata field names to SQL types, instead of
storing metadata as a single JSON blob. Use these when metadata follows a known, fixed schema and
individual fields should be queryable as SQL columns:

```pycon
>>> from docculus.store import TypedSQLiteDocumentStore
>>> from langchain_core.documents import Document
>>> schema = {"author": "TEXT", "year": "INTEGER"}
>>> with TypedSQLiteDocumentStore(metadata_schema=schema) as store:  # doctest: +SKIP
...     store.set_many(
...         [Document(id="1", page_content="Intro to Python", metadata={"author": "Alice"})]
...     )
...     print(len(store.filter(author="Alice")))
...
1

```

Use `DuckDBDocumentStore`/`SQLiteDocumentStore` instead of the `Typed...` variants when document
metadata does not follow a fixed schema.

## Wrapping an Arbitrary `persista` Store

`DocumentStore` wraps any `persista.store.BaseStore` instance, so you can use it with a
`persista` backend that has no dedicated `docculus` convenience class (e.g. Redis, PostgreSQL,
LMDB -- see the `persista` documentation for the full list):

```python
from docculus.store import DocumentStore
from persista.store import SomeStore  # any persista.store.BaseStore implementation

with DocumentStore(SomeStore(...)) as store:
    ...
```

`metadata_mode` controls how a document's metadata is represented in the underlying store's
values:

- `"flat"` (the default): each metadata field is stored as its own top-level key, alongside
  `page_content`
- `"single"`: the metadata dict is stored as a single nested JSON value under a `"metadata"` key

`InMemoryDocumentStore` always uses `"flat"`; `SQLiteDocumentStore`/`DuckDBDocumentStore` use
`"single"`; `TypedSQLiteDocumentStore`/`TypedDuckDBDocumentStore` use `"flat"`.

## Async Usage

Every store also exposes `a`-prefixed asynchronous methods (`aget`, `aset_many`, `acount`, ...)
that are coroutines (or async iterators), so they must be `await`ed and used from an `async`
function. The same store instance can be used from both sync and async code -- there is no
separate async class.

```pycon
>>> import asyncio
>>> from docculus.store import InMemoryDocumentStore
>>> from langchain_core.documents import Document
>>> async def main():  # doctest: +SKIP
...     async with InMemoryDocumentStore() as store:
...         await store.aset_many([Document(id="1", page_content="hello")])
...         print(await store.acount())
...         print(await store.aget("1"))
...
>>> asyncio.run(main())  # doctest: +SKIP
1
Document(id='1', page_content='hello', metadata={})

```

Using `async with` (as above) calls `aopen()` on entry and `aclose()` automatically on exit.

## Checking Which IDs Exist

`contains_many` checks a batch of IDs at once, returning a list of booleans in the same order as
the input, without fetching the documents themselves:

```pycon
>>> from docculus.store import InMemoryDocumentStore
>>> from langchain_core.documents import Document
>>> with InMemoryDocumentStore() as store:  # doctest: +SKIP
...     store.set_many(
...         [Document(id="1", page_content="a"), Document(id="2", page_content="b")]
...     )
...     print(store.contains_many(["1", "2", "3"]))
...
[True, True, False]

```

## Iterating Over a Store

`keys`, `values`, and `iter_batches` iterate over a store's content without loading everything
into memory at once. `iter_batches` is the scalable form of `values`, streaming documents from the
backend in chunks of `batch_size`:

```pycon
>>> from docculus.store import InMemoryDocumentStore
>>> from langchain_core.documents import Document
>>> with InMemoryDocumentStore() as store:  # doctest: +SKIP
...     store.set_many([Document(id=str(i), page_content=str(i)) for i in range(5)])
...     print(sorted(store.keys()))
...     for batch in store.iter_batches(batch_size=2):
...         print(len(batch))
...
['0', '1', '2', '3', '4']
2
2
1

```

## Custom Document Stores

To implement a store backed by something other than `persista`, subclass `BaseDocumentStore` and
implement all its abstract methods (`get`/`aget`, `set_many`/`aset_many`, `filter`/`afilter`,
`delete`/`adelete`, `delete_many`/`adelete_many`, `clear`/`aclear`, `contains`/`acontains`,
`contains_many`/`acontains_many`, `keys`/`akeys`, `iter_batches`/`aiter_batches`, `count`/`acount`,
`open`/`aopen`, `close`/`aclose`, and the `closed` property). `values`/`avalues` are provided by
the base class in terms of `iter_batches`/`aiter_batches`.

## Document Store Factories

`docculus.store.factory` decouples document-store creation from the rest of your code via
`BaseDocumentStoreFactory`, whose `make_document_store()` returns a configured
`BaseDocumentStore`:

- `DocumentStoreFactory`: wraps an already-built `BaseDocumentStore` instance and returns it as-is
- `ConfigurableDocumentStoreFactory`: accepts either a `BaseDocumentStore` instance or an
  `objectory`-style config `dict` (with a `"_target_"` key), resolved on each call
- `InMemoryDocumentStoreFactory`, `SQLiteDocumentStoreFactory`, `DuckDBDocumentStoreFactory`,
  `TypedSQLiteDocumentStoreFactory`, `TypedDuckDBDocumentStoreFactory`: build a fresh instance of
  the corresponding ready-to-use store on each call
- `StoreDocumentStoreFactory`: builds a `DocumentStore` from a
  `persista.store.factory.BaseStoreFactory`, useful when the backing key-value store itself needs
  to be freshly created (e.g. a new connection) each time

```pycon
>>> from docculus.store.factory import InMemoryDocumentStoreFactory
>>> factory = InMemoryDocumentStoreFactory()
>>> store = factory.make_document_store()

```

## API Reference

See the [reference documentation](../refs/store.md) for the full API.

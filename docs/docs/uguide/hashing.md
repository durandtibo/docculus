# Document IDs and Hashing

:book: This page describes `docculus.document` (per-document predicates and ID generation) and
`docculus.hashing` (content hashing), which together provide the building blocks for assigning
stable identifiers to [LangChain](https://python.langchain.com/) `Document` objects and detecting
identical content.

**Prerequisites:** You'll need to know a bit of Python and be familiar with `Document` objects.

## Overview

- `docculus.document`: per-document predicates and generators -- `is_empty`,
  `is_whitespace_only`, content length (`get_length`, `get_lengths`, `get_lengths_with_ids`,
  `get_shortest_document`, `get_longest_document`), and ID generation (`generate_id`,
  `generate_deterministic_id`, `generate_random_id`)
- `docculus.hashing`: content hashing -- `hash_document`, `hash_documents`, and `DocumentHasher`
  (a `coola` hasher-registry integration)

For corpus-wide (not per-document) statistics and duplicate detection, see the
[corpus analysis user guide](analysis.md).

## Generating Document IDs

`generate_id` assigns a UUID string to a document, dispatching to one of two strategies:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.document import generate_id
>>> doc = Document(page_content="Hello", metadata={"source": "cats.txt"})
>>> generate_id(doc, mode="deterministic") == generate_id(doc, mode="deterministic")
True

```

- `generate_deterministic_id` (`mode="deterministic"`, the default): derives the ID from the
  document's `page_content` and `metadata`, so re-generating an ID for the same content always
  returns the same value. Useful for idempotent indexing -- adding the same document twice yields
  the same ID, which upserts rather than duplicates.
- `generate_random_id` (`mode="random"`): generates a fresh, unrelated UUID on every call,
  ignoring the document's content.

In practice, [`assign_ids`](transform.md) is usually the more convenient entry point, since it
applies `generate_id` to every document in a list that doesn't already have one.

## Per-Document Length and Emptiness Checks

`is_empty` checks whether a document's `page_content` is the empty string (or not a string at
all, e.g. `None`); pass `treat_whitespace_as_empty=True` to also treat whitespace-only content as
empty. `is_whitespace_only` checks specifically for non-empty, whitespace-only content:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.document import is_empty, is_whitespace_only
>>> is_empty(Document(page_content=""))
True
>>> is_whitespace_only(Document(page_content="  \n"))
True

```

`get_length`/`get_lengths`/`get_lengths_with_ids` compute character counts of `page_content`; a
document whose `page_content` isn't a string counts as length `0`:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.document import get_lengths_with_ids
>>> docs = [
...     Document(id="a", page_content="hello"),
...     Document(id="b", page_content="hello world"),
... ]
>>> get_lengths_with_ids(docs)
[('a', 5), ('b', 11)]

```

`get_shortest_document`/`get_longest_document` stream through an iterable of documents in `O(1)`
memory and return the shortest/longest one, optionally skipping empty (or whitespace-only)
documents via `ignore_empty`/`treat_whitespace_as_empty`.

## Content Hashing

`hash_document` computes a stable, reproducible hex-string hash from a document's `page_content`
and `metadata` (serialized with sorted keys, so metadata key order doesn't affect the hash):

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.hashing import hash_document
>>> doc = Document(page_content="Hello", metadata={"source": "cats.txt"})
>>> len(hash_document(doc))
64

```

`hash_documents` hashes a list of documents into a single hash, order-sensitive (hashing each
document individually via `hash_document`, then combining the results). `length` (default `64`,
must be even and between `2` and `128`) controls the hex-string length for both functions.

`hash_document_to_uuid` (in `docculus.hashing`) is the UUID-formatted counterpart used internally
by `generate_deterministic_id`: it derives a stable `uuid.uuid5`-based UUID from the same
`page_content`/`metadata` combination, suitable for direct assignment to `Document.id`.

### Integrating with `coola`

`DocumentHasher` registers `Document` hashing with `coola`'s hasher registry (importing
`docculus.hashing` does this automatically at import time), so `Document` objects can be hashed
through `coola`'s generic hashing APIs:

```pycon
>>> from langchain_core.documents import Document
>>> from coola.hashing import HasherRegistry
>>> from docculus.hashing import DocumentHasher
>>> registry = HasherRegistry()
>>> hasher = DocumentHasher()
>>> doc = Document(page_content="hello", metadata={"source": "test"})
>>> len(hasher.hash(doc, registry=registry))
64

```

## API Reference

See the [reference documentation](../refs/document.md) and
[reference documentation](../refs/hashing.md) for the full API.

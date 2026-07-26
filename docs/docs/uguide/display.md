# Terminal Display

:book: This page describes the `docculus.display` package, which provides
[`rich`](https://rich.readthedocs.io/)-based pretty-printers for documents and their metadata.

**Prerequisites:** You'll need to know a bit of Python, and the `rich` extra (`docculus[rich]`)
must be installed.

## Overview

`docculus.display` provides three printing functions, all rendering to a `rich.console.Console`
(the current active console, via `rich.get_console()`, if none is passed explicitly):

- `print_document`: a single document as a bordered panel
- `print_documents`: an iterable of documents, one panel each
- `print_documents_metadata`: a compact, one-line-per-document metadata summary

## Printing a Single Document

`print_document` renders a document as a panel titled with its `id`, containing a `content` panel
(truncated on a word boundary at `max_length` characters, annotated with the omitted character
count) and, if metadata is non-empty, a `metadata` panel with entries sorted by key:

```python
from langchain_core.documents import Document
from docculus.display import print_document

doc = Document(id="1", page_content="hello world", metadata={"author": "Alice"})
print_document(doc, max_length=500)
```

Pass `compact_metadata=True` to render metadata as a single dimmed line instead of a nested panel.

## Printing Multiple Documents

`print_documents` renders each document in an iterable with `print_document`, one panel per
document, printed in order to the same console:

```python
from langchain_core.documents import Document
from docculus.display import print_documents

docs = [Document(id="1", page_content="hello"), Document(id="2", page_content="world")]
print_documents(docs)
```

## Printing Metadata Only

`print_documents_metadata` renders a single panel with one line per document: its `id` (if
present) followed by its metadata entries, sorted by key, joined by `separator` (`"•"` by
default). Documents with no metadata show a dimmed placeholder:

```python
from langchain_core.documents import Document
from docculus.display import print_documents_metadata

docs = [
    Document(id="1", page_content="hello", metadata={"author": "Alice", "year": 2020})
]
print_documents_metadata(docs, separator=" | ")
```

## API Reference

See the [reference documentation](../refs/display.md) for the full API.

# Validation

:book: This page describes the `docculus.validation` package, which checks that documents sharing
the same `id` agree on their `page_content` and `metadata`.

**Prerequisites:** You'll need to know a bit of Python and be familiar with
[LangChain](https://python.langchain.com/) `Document` objects.

## Overview

It's easy for a pipeline to accidentally produce two documents with the same `id` but different
content -- for example, if content is re-parsed with a different configuration but IDs are
generated deterministically from a source path rather than the content itself.
`validate_document_consistency` catches this before it silently overwrites data in a document
store.

## Checking Consistency

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.validation import validate_document_consistency
>>> docs = [
...     Document(id="1", page_content="hello"),
...     Document(id="1", page_content="hello"),
... ]
>>> validate_document_consistency(docs)
True

```

Documents are compared via a canonical JSON serialization of `metadata` (so key order doesn't
matter), and `id=None` documents are ignored, since `None` doesn't identify a single logical
document.

By default, `validate_document_consistency` logs a warning for each inconsistency found and
returns `False` if at least one was found, without raising:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.validation import validate_document_consistency
>>> docs = [
...     Document(id="1", page_content="hello"),
...     Document(id="1", page_content="goodbye"),
... ]
>>> validate_document_consistency(docs)
False

```

Pass `raise_error=True` to instead raise `DocumentConsistencyError` on the first inconsistency
found:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.validation import DocumentConsistencyError, validate_document_consistency
>>> docs = [
...     Document(id="1", page_content="hello"),
...     Document(id="1", page_content="goodbye"),
... ]
>>> try:
...     validate_document_consistency(docs, raise_error=True)
... except DocumentConsistencyError as e:
...     print("inconsistent")
...
inconsistent

```

## API Reference

See the [reference documentation](../refs/validation.md) for the full API.

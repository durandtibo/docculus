# Document Transforms

:book: This page describes the `docculus.transform` package, which provides functions that take a
list of documents and return a new (or, in a couple of cases, mutated) list: ID assignment,
deduplication, filtering, sorting, truncation, and LLM-friendly formatting.

**Prerequisites:** You'll need to know a bit of Python and be familiar with
[LangChain](https://python.langchain.com/) `Document` objects.

## Overview

Unlike `docculus.analysis` (read-only inspection), functions in `docculus.transform` produce a
new document list, or mutate the input list in place and return it, so the return value should
generally not be ignored:

- `assign_ids`/`copy_ids_to_metadata`: assign or propagate document IDs (mutate in place)
- `deduplicate_documents`: remove exact duplicates (new list)
- `filter_by_metadata`, `filter_by_metadata_range`, `filter_by_metadata_values`: keep only
  matching documents (new list)
- `sort_by_metadata`: order documents by a metadata field (new list)
- `truncate_documents`: cap `page_content` length (new list)
- `format_documents` and its `_as_xml`/`_as_markdown`/`_as_json` variants: concatenate documents
  into a single string for an LLM prompt

## Assigning IDs

`assign_ids` sets `id` on every document that doesn't already have one, using
[`generate_id`](hashing.md) internally. It mutates the input list in place and also returns it:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.transform import assign_ids
>>> docs = assign_ids([Document(page_content="hello")])
>>> len(docs[0].id)
36

```

`mode` (forwarded to `generate_id`) controls whether the ID is `"deterministic"` (derived from
content, the default) or `"random"`. Pass `force=True` to regenerate IDs even for documents that
already have one.

`copy_ids_to_metadata` copies each document's `id` into its metadata under `metadata_key`
(`"source_id"` by default). This is useful before running a text splitter: splitters generally
propagate a parent document's metadata onto every chunk, but not its `id` -- storing the parent id
in metadata first means every chunk keeps a reference back to its source document:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.transform import copy_ids_to_metadata
>>> docs = copy_ids_to_metadata([Document(id="doc-1", page_content="hello")])
>>> docs[0].metadata["source_id"]
'doc-1'

```

Documents whose `id` is `None` are left untouched, so no key is added for them.

## Deduplication

`deduplicate_documents` removes duplicates from a list, keeping the first occurrence. Two
documents are duplicates only if their `id`, `page_content`, and `metadata` are all equal
(`metadata` is compared via canonical JSON serialization, so key order doesn't matter):

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.transform import deduplicate_documents
>>> docs = [
...     Document(id="a", page_content="hello"),
...     Document(id="a", page_content="hello"),
...     Document(id="b", page_content="world"),
... ]
>>> len(deduplicate_documents(docs))
2

```

Pass `log=True` to log the initial/final document counts and the number of duplicates removed.

## Filtering

`filter_by_metadata` keeps documents whose metadata has an exact value for a given key; documents
missing the key are excluded:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.transform import filter_by_metadata
>>> docs = [
...     Document(page_content="a", metadata={"author": "Alice"}),
...     Document(page_content="b", metadata={"author": "Bob"}),
... ]
>>> len(filter_by_metadata(docs, "author", "Alice"))
1

```

`filter_by_metadata_range` keeps documents whose metadata value falls within `[lower, upper]`
(either bound may be `None` for no constraint on that side); `filter_by_metadata_values` keeps
documents whose metadata value is a member of a given `set`. Both also exclude documents missing
the key.

## Sorting

`sort_by_metadata` sorts documents by the value of a metadata key, ascending by default:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.transform import sort_by_metadata
>>> docs = [
...     Document(page_content="b", metadata={"year": 2020}),
...     Document(page_content="a", metadata={"year": 2010}),
... ]
>>> [d.page_content for d in sort_by_metadata(docs, "year")]
['a', 'b']

```

`keep_missing=True` (the default) places documents without the key at the end of the result;
`keep_missing=False` excludes them instead. `reverse=True` sorts descending.

## Truncating

`truncate_documents` caps each document's `page_content` at `max_length` characters, optionally
appending a `suffix` (included within `max_length`) to truncated documents:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.transform import truncate_documents
>>> docs = [Document(page_content="hello world")]
>>> truncate_documents(docs, max_length=8, suffix="...")[0].page_content
'hello...'

```

## Formatting for an LLM Prompt

`format_documents` concatenates a list of documents into a single LLM-friendly string, dispatching
to one of three renderers based on `output_format`:

```python
from langchain_core.documents import Document
from docculus.transform import format_documents

docs = [Document(id="1", page_content="hello", metadata={"author": "Alice"})]
format_documents(docs, output_format="markdown", include_metadata=True)
```

- `format_documents_as_xml` (`output_format="xml"`, the default): each document as a `<document>`
  block, with metadata rendered as `key: value` lines above the content when `include_metadata=True`
- `format_documents_as_markdown` (`output_format="markdown"`): each document under its own
  `## Document N` heading, with metadata as a bullet list
- `format_documents_as_json` (`output_format="json"`): a JSON array of `{"id", "content"}` objects
  (plus `"metadata"` when `include_metadata=True`)

All three sort metadata keys alphabetically and return an empty result (`""` or `"[]"`) for an
empty input.

## API Reference

See the [reference documentation](../refs/transform.md) for the full API.

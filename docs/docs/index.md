# Home

<p align="center">
    <a href="https://github.com/durandtibo/docculus/actions/workflows/ci.yaml">
        <img alt="CI" src="https://github.com/durandtibo/docculus/actions/workflows/ci.yaml/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/docculus/actions/workflows/nightly-tests.yaml">
        <img alt="Nightly Tests" src="https://github.com/durandtibo/docculus/actions/workflows/nightly-tests.yaml/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/docculus/actions/workflows/nightly-package.yaml">
        <img alt="Nightly Package Tests" src="https://github.com/durandtibo/docculus/actions/workflows/nightly-package.yaml/badge.svg">
    </a>
    <a href="https://codecov.io/gh/durandtibo/docculus">
        <img alt="Codecov" src="https://codecov.io/gh/durandtibo/docculus/branch/main/graph/badge.svg">
    </a>
    <br/>
    <a href="https://durandtibo.github.io/docculus/">
        <img alt="Documentation" src="https://github.com/durandtibo/docculus/actions/workflows/docs.yaml/badge.svg">
    </a>
    <a href="https://durandtibo.github.io/docculus/dev/">
        <img alt="Documentation" src="https://github.com/durandtibo/docculus/actions/workflows/docs-dev.yaml/badge.svg">
    </a>
    <br/>
    <a href="https://github.com/psf/black">
        <img  alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
    </a>
    <a href="https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings">
        <img  alt="Doc style: google" src="https://img.shields.io/badge/%20style-google-3666d6.svg">
    </a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" style="max-width:100%;">
    </a>
    <a href="https://github.com/guilatrova/tryceratops">
        <img  alt="try/except style: tryceratops" src="https://img.shields.io/badge/try%2Fexcept%20style-tryceratops%20%F0%9F%A6%96%E2%9C%A8-black">
    </a>
    <br/>
    <a href="https://pypi.org/project/docculus/">
        <img alt="PYPI version" src="https://img.shields.io/pypi/v/docculus">
    </a>
    <a href="https://pypi.org/project/docculus/">
        <img alt="Python" src="https://img.shields.io/pypi/pyversions/docculus.svg">
    </a>
    <a href="https://opensource.org/licenses/BSD-3-Clause">
        <img alt="BSD-3-Clause" src="https://img.shields.io/pypi/l/docculus">
    </a>
    <br/>
    <a href="https://pepy.tech/project/docculus">
        <img  alt="Downloads" src="https://static.pepy.tech/badge/docculus">
    </a>
    <a href="https://pepy.tech/project/docculus">
        <img  alt="Monthly downloads" src="https://static.pepy.tech/badge/docculus/month">
    </a>
    <br/>
</p>

## Overview

`docculus` is a lightweight library for working with
[LangChain](https://python.langchain.com/) `Document` objects: persisting them in a store,
assigning stable IDs, hashing and deduplicating them, inspecting a corpus for data-quality
issues, and reshaping document lists for downstream use (filtering, sorting, truncating,
formatting for an LLM prompt).

**Quick Links:**

- [User Guide](uguide/store.md)
- [Installation](get_started.md)
- [Features](#features)
- [Contributing](#contributing)

## Why docculus?

Working with LangChain documents in a real pipeline means solving the same handful of problems
every time: where do documents live between runs, how do you assign them a stable `id` so
re-indexing doesn't create duplicates, and how do you tell whether a scraped/parsed corpus is
actually any good. `docculus` provides small, composable building blocks for each of these:

**Persist documents, keyed by `id`:**

```pycon
>>> from docculus.store import InMemoryDocumentStore
>>> from langchain_core.documents import Document
>>> with InMemoryDocumentStore() as store:  # doctest: +SKIP
...     store.set_many(
...         [Document(id="1", page_content="hello", metadata={"author": "Alice"})]
...     )
...     store.get("1")
...
Document(id='1', page_content='hello', metadata={'author': 'Alice'})

```

**Assign a stable, content-derived `id`:**

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.transform import assign_ids
>>> docs = assign_ids([Document(page_content="hello")])
>>> len(docs[0].id)
36

```

**Check a corpus for empty content, duplicates, and metadata gaps:**

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.analysis import compute_content_stats_exact
>>> docs = [Document(id="a", page_content="hello"), Document(id="b", page_content="hello")]
>>> compute_content_stats_exact(docs)["count"]
2

```

See the [user guide](uguide/store.md) for detailed examples.

## Features

`docculus` provides a comprehensive set of utilities for working with LangChain documents:

### 🗄️ **Document Stores**

A consistent `BaseDocumentStore` interface for persisting `Document` objects, keyed by `id`,
backed by [`persista`](https://pypi.org/project/persista/) key-value stores, with both
synchronous and `a`-prefixed asynchronous methods:

- `DocumentStore`: a generic wrapper around any `persista.store.BaseStore`
- Ready-to-use backends: `InMemoryDocumentStore`, `SQLiteDocumentStore`, `DuckDBDocumentStore`,
  and their "typed" variants (`TypedSQLiteDocumentStore`, `TypedDuckDBDocumentStore`), which map
  metadata fields onto native SQL columns instead of a single JSON blob
- Factories (`docculus.store.factory`) to decouple document-store construction from the rest of
  your code

[Learn more →](uguide/store.md)

### 🔍 **Corpus Analysis**

Read-only, streaming inspection utilities for a corpus of documents:

- `compute_content_stats_exact` / `compute_content_stats_approx`: content length, duplicate, and
  data-quality statistics, with an exact (in-memory) and an approximate (Bloom filter +
  reservoir sampling, fixed memory) variant
- `compute_metadata_stats`: per-key metadata coverage and sample values
- `find_duplicate_document_ids`, `find_empty_documents` / `find_empty_document_ids`
- `print_content_stats_report` / `print_metadata_stats_report`: render the stats above as a
  terminal report (requires the `rich` extra)

[Learn more →](uguide/analysis.md)

### ✂️ **Document Transforms**

Functions that take a list of documents and return a new (or mutated) list:

- `assign_ids` / `copy_ids_to_metadata`: stable ID assignment and propagation to chunks
- `deduplicate_documents`: remove exact `(id, page_content, metadata)` duplicates
- `filter_by_metadata`, `filter_by_metadata_range`, `filter_by_metadata_values`
- `sort_by_metadata`, `truncate_documents`
- `format_documents` (and its `_as_xml` / `_as_markdown` / `_as_json` variants): concatenate
  documents into a single LLM-friendly string

[Learn more →](uguide/transform.md)

### 🧾 **Hashing and IDs**

- `generate_id` / `generate_deterministic_id` / `generate_random_id`: assign a UUID to a
  document, deterministically derived from its content when desired
- `hash_document` / `hash_documents`: stable content hashes for a document or list of documents
- `DocumentHasher`: integration with `coola`'s hasher registry

[Learn more →](uguide/hashing.md)

### 🖨️ **Terminal Display**

`rich`-based pretty-printers for documents and their metadata (requires the `rich` extra):
`print_document`, `print_documents`, `print_documents_metadata`.

[Learn more →](uguide/display.md)

### ✅ **Validation**

`validate_document_consistency`: check that documents sharing the same `id` agree on
`page_content` and `metadata`.

[Learn more →](uguide/validation.md)

## Contributing

Contributions are welcome! We appreciate bug fixes, feature additions, documentation improvements,
and more. Please check
the [contributing guidelines](https://github.com/durandtibo/docculus/blob/main/CONTRIBUTING.md) for
details on:

- Setting up the development environment
- Code style and testing requirements
- Submitting pull requests

Whether you're fixing a bug or proposing a new feature, please open an issue first to discuss
your changes.

## API Stability

:warning: **Important**: As `docculus` is under active development, its API is not yet stable and may
change between releases. We recommend pinning a specific version in your project’s dependencies to
ensure consistent behavior.

## License

`docculus` is licensed under BSD 3-Clause "New" or "Revised" license available
in [LICENSE](https://github.com/durandtibo/docculus/blob/main/LICENSE)
file.

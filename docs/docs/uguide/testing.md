# Testing Helpers

:book: This page describes `docculus.testing.fixtures`, which provides `pytest` markers to skip
tests based on whether an optional dependency is installed.

**Prerequisites:** You'll need to know a bit of Python and [`pytest`](https://docs.pytest.org/).
`pytest` must be installed to use these fixtures; `docculus.testing` is not a runtime dependency
of `docculus` itself.

## Overview

Several `docculus` features depend on optional packages: `docculus.store`'s ready-to-use document
stores require `persista`, `docculus.utils.fake` requires `faker`, and `docculus.analysis`'s
report-printing functions require `rich`. `docculus.testing.fixtures` exposes, for each of these,
a pair of `pytest` markers:

- `<dep>_available`: skip the test unless `<dep>` is installed
- `<dep>_not_available`: skip the test if `<dep>` is installed

Markers are currently provided for `faker` and `persista`: `faker_available`/`faker_not_available`
and `persista_available`/`persista_not_available`.

## Skipping Tests Based on Optional Dependencies

Use `<dep>_available` to only run a test when the corresponding package is installed, for example
a test that exercises `InMemoryDocumentStore` (which requires `persista`):

```python
from docculus.store import InMemoryDocumentStore
from docculus.testing.fixtures import persista_available


@persista_available
def test_in_memory_document_store_set_get():
    with InMemoryDocumentStore() as store:
        store.set_many([...])
```

Use `<dep>_not_available` for the opposite case, e.g. verifying that a helpful error is raised
when a required optional dependency is missing:

```python
import pytest

from docculus.testing.fixtures import persista_not_available


@persista_not_available
def test_in_memory_document_store_requires_persista():
    with pytest.raises(RuntimeError, match="'persista' package is required"):
        from docculus.store import InMemoryDocumentStore

        InMemoryDocumentStore()
```

## Available Markers

Import markers directly from `docculus.testing.fixtures`, for example:

```python
from docculus.testing.fixtures import faker_available, persista_available
```

## Generating Fake Documents

`docculus.utils.fake.generate_fake_documents` (requires the `faker` extra, `docculus[faker]`)
generates synthetic `Document` objects for tests and examples, each with a unique `id`
(`"doc-{i}"`), a Faker-generated paragraph as content, and metadata containing a fake author and
topic:

```python
from docculus.utils.fake import generate_fake_documents

docs = generate_fake_documents(n=10)
```

Content is not guaranteed to be unique across documents -- `Faker.paragraph()` has no built-in
uniqueness constraint, so deduplicate the result yourself (see
[`deduplicate_documents`](transform.md)) if strict uniqueness matters.

## API Reference

See the [reference documentation](../refs/testing.md) and
[reference documentation](../refs/utils.md) for the full API.

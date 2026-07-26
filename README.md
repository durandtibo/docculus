# docculus

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

A python library for LangChain documents

## Overview

`docculus` provides utilities for working with `langchain_core.documents.Document` objects:
analyzing, transforming, hashing, validating, and displaying them.

- `docculus.analysis` — content/metadata statistics, duplicate and empty-document detection
- `docculus.transform` — filter, sort, deduplicate, truncate, assign ids, and format documents
  into LLM-friendly strings (XML, Markdown, JSON)
- `docculus.hashing` — deterministic hashing of documents (including a stable UUID variant)
- `docculus.validation` — consistency checks across documents sharing an id
- `docculus.display` — pretty-print documents and their metadata to the terminal
- `docculus.utils` — helpers such as fake document generation for testing

## Installation

```shell
pip install docculus
```

## Quick start

```python
from langchain_core.documents import Document
from docculus.analysis import compute_content_stats_exact
from docculus.transform import deduplicate_documents, format_documents

docs = [
    Document(id="1", page_content="The cat sat on the mat."),
    Document(id="2", page_content="The cat sat on the mat."),
    Document(id="3", page_content="The dog chased the ball."),
]

stats = compute_content_stats_exact(docs)
print(stats["count"], stats["duplicate_count"])

unique_docs = deduplicate_documents(docs)
print(format_documents(unique_docs, output_format="markdown"))
```

## Contributing

Contributions are welcome! We appreciate bug fixes, feature additions, documentation improvements,
and more. Please check the [contributing guidelines](CONTRIBUTING.md) for details on:

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

`docculus` is licensed under BSD 3-Clause "New" or "Revised" license available in [LICENSE](LICENSE)
file.

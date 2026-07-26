from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from coola.testing.fixtures import rich_available
from coola.utils.imports import is_rich_available
from langchain_core.documents import Document

from docculus.display.documents import print_documents

if TYPE_CHECKING:
    from collections.abc import Generator

if is_rich_available():
    from rich.console import Console


MODULE = "docculus.display.documents"


def _make_doc(
    id_: str = "1", content: str = "Hello world", metadata: dict | None = None
) -> Document:
    return Document(id=id_, page_content=content, metadata=metadata or {})


#####################################
#     Tests for print_documents    #
#####################################


@rich_available
def test_print_documents() -> None:
    print_documents([_make_doc()])


@rich_available
def test_print_documents_returns_none() -> None:
    assert print_documents([_make_doc()]) is None


@rich_available
def test_print_documents_empty_list() -> None:
    print_documents([])


@rich_available
def test_print_documents_uses_custom_console() -> None:
    custom = MagicMock(spec=Console)
    print_documents([_make_doc(id_="1"), _make_doc(id_="2")], console=custom)
    assert custom.print.call_count == 2


@rich_available
def test_print_documents_resolves_console_once() -> None:
    """The console is resolved a single time and shared across all
    documents rather than re-fetched per document."""
    with patch(f"{MODULE}.get_console") as mock_get_console:
        mock_get_console.return_value = MagicMock(spec=Console)
        print_documents([_make_doc(id_="1"), _make_doc(id_="2")])
    mock_get_console.assert_called_once()


@rich_available
def test_print_documents_passes_max_length() -> None:
    with patch(f"{MODULE}.print_document") as mock_print_document:
        print_documents([_make_doc()], max_length=42)
    assert mock_print_document.call_args.kwargs["max_length"] == 42


@rich_available
def test_print_documents_passes_compact_metadata() -> None:
    with patch(f"{MODULE}.print_document") as mock_print_document:
        print_documents([_make_doc()], compact_metadata=True)
    assert mock_print_document.call_args.kwargs["compact_metadata"] is True


@rich_available
def test_print_documents_consumes_generator() -> None:
    def gen() -> Generator[Document, None, None]:
        yield _make_doc(id_="1")
        yield _make_doc(id_="2")

    custom = MagicMock(spec=Console)
    print_documents(gen(), console=custom)
    assert custom.print.call_count == 2


@rich_available
def test_print_documents_preserves_order() -> None:
    with patch(f"{MODULE}.print_document") as mock_print_document:
        docs = [_make_doc(id_="1"), _make_doc(id_="2"), _make_doc(id_="3")]
        print_documents(docs)
    called_docs = [call.args[0] for call in mock_print_document.call_args_list]
    assert called_docs == docs

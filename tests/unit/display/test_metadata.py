from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from coola.testing.fixtures import rich_available
from coola.utils.imports import is_rich_available
from langchain_core.documents import Document

from docculus.display import print_documents_metadata

if is_rich_available():
    from rich.console import Console, Group
    from rich.panel import Panel

MODULE = "docculus.display.metadata"


def _make_doc(
    id_: str = "1", content: str = "Hello world", metadata: dict | None = None
) -> Document:
    return Document(id=id_, page_content=content, metadata=metadata or {})


##############################################
#     Tests for print_documents_metadata     #
##############################################


@rich_available
def test_print_documents_metadata() -> None:
    print_documents_metadata([_make_doc()])


@rich_available
def test_print_documents_metadata_with_metadata() -> None:
    print_documents_metadata([_make_doc(metadata={"author": "Alice"})])


@rich_available
def test_print_documents_metadata_returns_none() -> None:
    assert print_documents_metadata([_make_doc()]) is None


@rich_available
def test_print_documents_metadata_empty_list() -> None:
    print_documents_metadata([])


@rich_available
def test_print_documents_metadata_multiple_documents() -> None:
    print_documents_metadata(
        [
            _make_doc(id_="1", metadata={"author": "Alice"}),
            _make_doc(id_="2", metadata={"author": "Bob", "year": 2024}),
            _make_doc(id_="3", metadata={}),
        ]
    )


@rich_available
def test_print_documents_metadata_custom_separator() -> None:
    print_documents_metadata([_make_doc(metadata={"author": "Alice", "year": 2024})], separator="|")


@rich_available
@pytest.mark.parametrize(
    "documents",
    [
        pytest.param([], id="no-documents"),
        pytest.param([_make_doc(metadata={})], id="no-metadata"),
        pytest.param([_make_doc(metadata={"author": "Alice"})], id="with-metadata"),
        pytest.param(
            [
                _make_doc(id_="1", metadata={"author": "Alice"}),
                _make_doc(id_="2", metadata={}),
            ],
            id="mixed-metadata",
        ),
    ],
)
def test_print_documents_metadata_renders_panel(documents: list[Document]) -> None:
    with patch(f"{MODULE}.get_console") as mock_get_console:
        mock_console = MagicMock(spec=Console)
        mock_get_console.return_value = mock_console
        print_documents_metadata(documents)
    panel: Panel = mock_console.print.call_args.args[0]
    assert isinstance(panel, Panel)
    assert isinstance(panel.renderable, Group)


@rich_available
def test_print_documents_metadata_uses_custom_console() -> None:
    custom = MagicMock(spec=Console)
    print_documents_metadata([_make_doc()], console=custom)
    custom.print.assert_called_once()


@rich_available
def test_print_documents_metadata_custom_console_not_shared() -> None:
    """A per-call console does not affect the shared instance."""
    custom = MagicMock(spec=Console)
    with patch(f"{MODULE}.get_console") as mock_get_console:
        mock_get_console.return_value = MagicMock(spec=Console)
        print_documents_metadata([_make_doc()], console=custom)
        assert mock_get_console.return_value is not custom


@rich_available
def test_print_documents_metadata_title_contains_count() -> None:
    custom = MagicMock(spec=Console)
    print_documents_metadata([_make_doc(), _make_doc(id_="2")], console=custom)
    panel: Panel = custom.print.call_args.args[0]
    assert "2" in panel.title


@rich_available
def test_print_documents_metadata_no_id_falls_back_to_index() -> None:
    custom = MagicMock(spec=Console)
    doc = Document(page_content="Hello", metadata={})
    print_documents_metadata([doc], console=custom)
    panel: Panel = custom.print.call_args.args[0]
    assert isinstance(panel.renderable, Group)

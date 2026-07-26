r"""Implement a document store backed by a ``persista`` key-value
store."""

from __future__ import annotations

__all__ = ["DocumentStore", "MetadataMode"]

from typing import TYPE_CHECKING, Any, Literal

from langchain_core.documents import Document

from docculus.store.base import BaseDocumentStore
from docculus.utils.imports import check_persista

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Generator, Iterator

    from persista.store import BaseStore


MetadataMode = Literal["single", "flat"]

_ID_KEY = "id"
_CONTENT_KEY = "page_content"
_METADATA_KEY = "metadata"


class DocumentStore(BaseDocumentStore):
    r"""Implement a document store backed by a
    :class:`persista.store.BaseStore`.

    Documents are keyed by their ``id`` in the underlying key-value
    store. ``metadata_mode`` controls how a document's metadata is
    represented in the stored value:

    - ``"single"``: the metadata dict is stored as a single nested
      value under the ``"metadata"`` key.
    - ``"flat"``: each metadata field is stored as its own top-level
      key in the stored value, alongside ``"page_content"``. This
      allows :meth:`filter` to be delegated to the underlying store's
      own ``filter`` method instead of being done client-side.

    Args:
        store: The underlying key-value store.
        metadata_mode: How document metadata is represented in the
            values stored in ``store``.
    """

    def __init__(self, store: BaseStore, metadata_mode: MetadataMode = "flat") -> None:
        check_persista()
        if metadata_mode not in ("single", "flat"):
            msg = f"Incorrect metadata_mode: {metadata_mode!r}. Expected 'single' or 'flat'"
            raise ValueError(msg)
        self._store = store
        self._metadata_mode: MetadataMode = metadata_mode

    @property
    def store(self) -> BaseStore:
        return self._store

    @property
    def metadata_mode(self) -> MetadataMode:
        return self._metadata_mode

    @staticmethod
    def _require_id(doc: Document) -> str:
        if doc.id is None:
            msg = "Document must have an 'id'"
            raise ValueError(msg)
        return doc.id

    def _to_value(self, doc: Document) -> dict[str, Any]:
        doc_id = self._require_id(doc)
        if self._metadata_mode == "single":
            return {
                _ID_KEY: doc_id,
                _CONTENT_KEY: doc.page_content,
                _METADATA_KEY: dict(doc.metadata),
            }
        return {_ID_KEY: doc_id, _CONTENT_KEY: doc.page_content, **doc.metadata}

    def _from_value(self, value: dict[str, Any]) -> Document:
        value = dict(value)
        doc_id = value.pop(_ID_KEY)
        content = value.pop(_CONTENT_KEY, "")
        metadata = value.pop(_METADATA_KEY, {}) if self._metadata_mode == "single" else value
        return Document(id=doc_id, page_content=content, metadata=metadata)

    def set_many(self, docs: list[Document]) -> None:
        self._store.set_many(
            {self._require_id(doc): self._to_value(doc) for doc in docs}, on_conflict="overwrite"
        )

    async def aset_many(self, docs: list[Document]) -> None:
        await self._store.aset_many(
            {self._require_id(doc): self._to_value(doc) for doc in docs}, on_conflict="overwrite"
        )

    def get(self, doc_id: str) -> Document | None:
        value = self._store.get(doc_id)
        return self._from_value(value) if value is not None else None

    async def aget(self, doc_id: str) -> Document | None:
        value = await self._store.aget(doc_id)
        return self._from_value(value) if value is not None else None

    def get_many(self, doc_ids: list[str]) -> list[Document | None]:
        return [
            self._from_value(value) if value is not None else None
            for value in self._store.get_many(doc_ids)
        ]

    async def aget_many(self, doc_ids: list[str]) -> list[Document | None]:
        return [
            self._from_value(value) if value is not None else None
            for value in await self._store.aget_many(doc_ids)
        ]

    def filter(self, **metadata_filters: Any) -> list[Document]:
        if self._metadata_mode == "flat":
            return [self._from_value(value) for value in self._store.filter(**metadata_filters)]
        return [
            doc
            for doc in (self._from_value(value) for value in self._store.filter())
            if all(doc.metadata.get(key) == val for key, val in metadata_filters.items())
        ]

    async def afilter(self, **metadata_filters: Any) -> list[Document]:
        if self._metadata_mode == "flat":
            return [
                self._from_value(value) for value in await self._store.afilter(**metadata_filters)
            ]
        return [
            doc
            for doc in (self._from_value(value) for value in await self._store.afilter())
            if all(doc.metadata.get(key) == val for key, val in metadata_filters.items())
        ]

    def delete(self, doc_id: str) -> None:
        self._store.delete(doc_id)

    async def adelete(self, doc_id: str) -> None:
        await self._store.adelete(doc_id)

    def delete_many(self, doc_ids: list[str]) -> None:
        self._store.delete_many(doc_ids)

    async def adelete_many(self, doc_ids: list[str]) -> None:
        await self._store.adelete_many(doc_ids)

    def clear(self) -> None:
        self._store.clear()

    async def aclear(self) -> None:
        await self._store.aclear()

    def contains(self, doc_id: str) -> bool:
        return self._store.contains(doc_id)

    async def acontains(self, doc_id: str) -> bool:
        return await self._store.acontains(doc_id)

    def contains_many(self, doc_ids: list[str]) -> list[bool]:
        return self._store.contains_many(doc_ids)

    async def acontains_many(self, doc_ids: list[str]) -> list[bool]:
        return await self._store.acontains_many(doc_ids)

    def keys(self) -> Iterator[str]:
        return self._store.keys()

    async def akeys(self) -> AsyncIterator[str]:
        async for key in self._store.akeys():
            yield key

    def iter_batches(self, batch_size: int = 32) -> Generator[list[Document], None, None]:
        for batch in self._store.iter_batches(batch_size=batch_size):
            yield [self._from_value(value) for value in batch.values()]

    async def aiter_batches(self, batch_size: int = 32) -> AsyncIterator[list[Document]]:
        async for batch in self._store.aiter_batches(batch_size=batch_size):
            yield [self._from_value(value) for value in batch.values()]

    def count(self) -> int:
        return self._store.count()

    async def acount(self) -> int:
        return await self._store.acount()

    def open(self) -> None:
        self._store.open()

    async def aopen(self) -> None:
        await self._store.aopen()

    def close(self) -> None:
        self._store.close()

    async def aclose(self) -> None:
        await self._store.aclose()

    @property
    def closed(self) -> bool:
        return self._store.closed

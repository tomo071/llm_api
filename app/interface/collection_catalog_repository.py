from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class ActiveCollectionRecord:
    id: int
    collection_name: str


IngestCollectionLookupStatus = Literal["active", "not_found", "deleted", "ambiguous"]


@dataclass(frozen=True)
class IngestCollectionLookup:
    status: IngestCollectionLookupStatus
    collection: ActiveCollectionRecord | None = None


class CollectionCatalogRepository(Protocol):
    def find_for_ingest(self, *, customer_id: str, use_type: int) -> IngestCollectionLookup: ...

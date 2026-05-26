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


@dataclass(frozen=True)
class GenerateCollectionRecord:
    id: int
    customer_id: str
    collection_name: str


GenerateCollectionLookupStatus = Literal["active", "not_found", "deleted"]


@dataclass(frozen=True)
class GenerateCollectionLookup:
    status: GenerateCollectionLookupStatus
    collection: GenerateCollectionRecord | None = None


@dataclass(frozen=True)
class CreatedCollectionRecord:
    id: int
    collection_name: str
    use_type: int


CreateCollectionCatalogStatus = Literal["created", "duplicate", "customer_not_found"]


@dataclass(frozen=True)
class CreateCollectionCatalogResult:
    status: CreateCollectionCatalogStatus
    collection: CreatedCollectionRecord | None = None


class CollectionCatalogRepository(Protocol):
    def find_for_ingest(self, *, customer_id: str, use_type: int) -> IngestCollectionLookup: ...

    def find_by_id_for_generate(self, *, reference_set_id: int) -> GenerateCollectionLookup: ...

    def create_active_collection(
        self,
        *,
        customer_id: str,
        collection_name: str,
        use_type: int,
    ) -> CreateCollectionCatalogResult: ...

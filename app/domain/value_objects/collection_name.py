from __future__ import annotations

from dataclasses import dataclass

from domain.errors import DomainValidationError


@dataclass(frozen=True)
class CollectionDisplayName:
    value: str

    @staticmethod
    def from_raw(raw: str) -> "CollectionDisplayName":
        v = (raw or "").strip()
        if not v:
            raise DomainValidationError("空にできません", field="name")
        return CollectionDisplayName(value=v)


@dataclass(frozen=True)
class QdrantCollectionName:
    value: str

    @staticmethod
    def from_parts(*, customer_id: str, display_name: str) -> "QdrantCollectionName":
        cid = (customer_id or "").strip()
        name = (display_name or "").strip()
        if not cid:
            raise DomainValidationError("空にできません", field="customer_id")
        if not name:
            raise DomainValidationError("空にできません", field="name")
        return QdrantCollectionName(value=f"collection{cid}_{name}")


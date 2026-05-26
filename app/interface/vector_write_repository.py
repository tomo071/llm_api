from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from interface.collection_repository import RepositoryError


@dataclass(frozen=True)
class ChunkPoint:
    point_id: str
    vector: list[float]
    text: str
    source_path: str
    chunk_index: int
    job_id: str
    collection_db_id: int


class VectorWriteRepository(Protocol):
    def upsert_chunks(self, *, collection_name: str, points: list[ChunkPoint]) -> None: ...

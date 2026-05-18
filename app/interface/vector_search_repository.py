from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from interface.collection_repository import RepositoryError


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    score: float


class VectorSearchRepository(Protocol):
    def search_similar(
        self,
        *,
        collection_name: str,
        query_vector: list[float],
        limit: int,
        score_threshold: float,
    ) -> list[RetrievedChunk]: ...

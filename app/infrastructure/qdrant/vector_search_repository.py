from __future__ import annotations

from dataclasses import dataclass

from qdrant_client import QdrantClient

from interface.collection_repository import RepositoryError
from interface.vector_search_repository import RetrievedChunk


@dataclass(frozen=True)
class QdrantVectorSearchRepository:
    client: QdrantClient

    def search_similar(
        self,
        *,
        collection_name: str,
        query_vector: list[float],
        limit: int,
        score_threshold: float,
    ) -> list[RetrievedChunk]:
        try:
            hits = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
        except Exception as e:
            raise RepositoryError("ベクトル検索中にQdrantでエラーが発生しました") from e

        chunks: list[RetrievedChunk] = []
        for hit in hits:
            payload = hit.payload or {}
            text = payload.get("text") or payload.get("content") or ""
            if not str(text).strip():
                continue
            chunks.append(RetrievedChunk(text=str(text), score=float(hit.score)))
        return chunks

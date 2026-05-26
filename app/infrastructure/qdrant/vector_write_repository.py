from __future__ import annotations

from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from interface.collection_repository import RepositoryError
from interface.vector_write_repository import ChunkPoint


@dataclass(frozen=True)
class QdrantVectorWriteRepository:
    client: QdrantClient

    def upsert_chunks(self, *, collection_name: str, points: list[ChunkPoint]) -> None:
        if not points:
            return

        qdrant_points = [
            PointStruct(
                id=point.point_id,
                vector=point.vector,
                payload={
                    "text": point.text,
                    "source_path": point.source_path,
                    "chunk_index": point.chunk_index,
                    "job_id": point.job_id,
                    "collection_db_id": point.collection_db_id,
                },
            )
            for point in points
        ]

        try:
            self.client.upsert(collection_name=collection_name, points=qdrant_points)
        except Exception as e:
            raise RepositoryError("ベクトル投入中にQdrantでエラーが発生しました") from e

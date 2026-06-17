from __future__ import annotations

from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, VectorParams

from interface.collection_repository import CollectionRepository, RepositoryError


@dataclass(frozen=True)
class QdrantCollectionRepository(CollectionRepository):
    client: QdrantClient
    vector_size: int = 1536

    def collection_exists(self, collection_name: str) -> bool:
        try:
            res = self.client.get_collections()
            return any(c.name == collection_name for c in res.collections)
        except Exception as e:  # pragma: no cover
            raise RepositoryError("コレクションの存在確認中にQdrantでエラーが発生しました") from e

    def create_collection(self, collection_name: str) -> None:
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
        except UnexpectedResponse as e:
            # 409 etc. should be handled by usecase via existence check; still wrap here.
            raise RepositoryError("Qdrantがコレクション作成を拒否しました") from e
        except Exception as e:  # pragma: no cover
            raise RepositoryError("コレクション作成中にQdrantでエラーが発生しました") from e

    def delete_collection(self, collection_name: str) -> None:
        try:
            self.client.delete_collection(collection_name=collection_name)
        except UnexpectedResponse as e:
            raise RepositoryError("Qdrantがコレクション削除を拒否しました") from e
        except Exception as e:  # pragma: no cover
            raise RepositoryError("コレクション削除中にQdrantでエラーが発生しました") from e # pragma: no cover

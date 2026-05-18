from __future__ import annotations

from dataclasses import dataclass

from domain.validation.collection_validation import require_non_empty
from domain.value_objects.collection_name import CollectionDisplayName, QdrantCollectionName
from interface.collection_catalog_repository import CollectionCatalogRepository
from interface.collection_repository import RepositoryError
from interface.embedding_client import EmbeddingClient, EmbeddingClientError
from interface.llm_client import LlmClient, LlmClientError
from interface.vector_search_repository import VectorSearchRepository
from usecase.create_collection import ExternalServiceError, InvalidApiKeyError, UsecaseError

GENERATE_SEARCH_CHUNK_LIMIT = 1000
GENERATE_SIMILARITY_THRESHOLD = 7.5


class ReferenceSetNotFoundError(UsecaseError):
    """指定の reference_set_id に該当するコレクションがない。"""


class ReferenceSetDeletedError(UsecaseError):
    """reference_set が論理削除済み。"""


@dataclass(frozen=True)
class GenerateResult:
    content: str


@dataclass(frozen=True)
class GenerateUsecase:
    collection_catalog_repository: CollectionCatalogRepository
    vector_search_repository: VectorSearchRepository
    embedding_client: EmbeddingClient
    llm_client: LlmClient
    service_api_key: str

    def execute(
        self,
        *,
        api_key: str | None,
        prompt: str | None,
        reference_set_id: int | None,
    ) -> GenerateResult:
        api_key_v = require_non_empty(api_key, field="API_key")
        prompt_v = require_non_empty(prompt, field="prompt")

        if api_key_v != self.service_api_key:
            raise InvalidApiKeyError("APIキーが無効です")

        context: str | None = None
        if reference_set_id is not None:
            context = self._build_reference_context(
                reference_set_id=reference_set_id,
                prompt=prompt_v,
            )

        try:
            content = self.llm_client.generate(prompt=prompt_v, context=context)
        except LlmClientError as e:
            raise ExternalServiceError(str(e)) from e

        return GenerateResult(content=content)

    def _build_reference_context(self, *, reference_set_id: int, prompt: str) -> str:
        try:
            lookup = self.collection_catalog_repository.find_by_id_for_generate(
                reference_set_id=reference_set_id,
            )
        except Exception as e:
            raise ExternalServiceError("コレクション情報の取得に失敗しました") from e

        if lookup.status == "not_found":
            raise ReferenceSetNotFoundError("指定された reference_set が見つかりません")
        if lookup.status == "deleted":
            raise ReferenceSetDeletedError("reference_set は論理削除されています")
        if lookup.collection is None:
            raise ExternalServiceError("コレクション情報の取得に失敗しました")

        display = CollectionDisplayName.from_raw(lookup.collection.collection_name)
        qdrant_name = QdrantCollectionName.from_parts(
            customer_id=lookup.collection.customer_id,
            display_name=display.value,
        )

        try:
            query_vector = self.embedding_client.embed_text(prompt)
        except EmbeddingClientError as e:
            raise ExternalServiceError(str(e)) from e

        score_threshold = GENERATE_SIMILARITY_THRESHOLD / 10.0
        try:
            chunks = self.vector_search_repository.search_similar(
                collection_name=qdrant_name.value,
                query_vector=query_vector,
                limit=GENERATE_SEARCH_CHUNK_LIMIT,
                score_threshold=score_threshold,
            )
        except RepositoryError as e:
            raise ExternalServiceError(str(e)) from e

        if not chunks:
            return ""

        return "\n\n".join(chunk.text for chunk in chunks)

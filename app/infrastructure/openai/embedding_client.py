from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from interface.embedding_client import EmbeddingClientError


_EMBEDDING_BATCH_SIZE = 64


@dataclass(frozen=True)
class OpenAIEmbeddingClient:
    api_key: str
    model: str = "text-embedding-3-small"

    def embed_text(self, text: str) -> list[float]:
        vectors = self.embed_texts([text])
        return vectors[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            client = OpenAI(api_key=self.api_key)
            all_vectors: list[list[float]] = []
            for start in range(0, len(texts), _EMBEDDING_BATCH_SIZE):
                batch = texts[start : start + _EMBEDDING_BATCH_SIZE]
                response = client.embeddings.create(input=batch, model=self.model)
                ordered = sorted(response.data, key=lambda item: item.index)
                all_vectors.extend(list(item.embedding) for item in ordered)
            return all_vectors
        except Exception as e:
            raise EmbeddingClientError("埋め込みベクトルの生成に失敗しました") from e

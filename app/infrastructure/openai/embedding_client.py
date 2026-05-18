from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from interface.embedding_client import EmbeddingClientError


@dataclass(frozen=True)
class OpenAIEmbeddingClient:
    api_key: str
    model: str = "text-embedding-3-small"

    def embed_text(self, text: str) -> list[float]:
        try:
            client = OpenAI(api_key=self.api_key)
            response = client.embeddings.create(input=text, model=self.model)
            return list(response.data[0].embedding)
        except Exception as e:
            raise EmbeddingClientError("埋め込みベクトルの生成に失敗しました") from e

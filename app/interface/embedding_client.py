from __future__ import annotations

from typing import Protocol


class EmbeddingClientError(Exception):
    pass


class EmbeddingClient(Protocol):
    def embed_text(self, text: str) -> list[float]: ...

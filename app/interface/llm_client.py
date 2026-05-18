from __future__ import annotations

from typing import Protocol


class LlmClientError(Exception):
    pass


class LlmClient(Protocol):
    def generate(self, *, prompt: str, context: str | None = None) -> str: ...

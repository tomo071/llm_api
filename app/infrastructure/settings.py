from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _optional_env(name: str) -> str | None:
    v = os.getenv(name)
    if v is None or not v.strip():
        return None
    return v.strip()


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if v is None or not v.strip():
        raise RuntimeError(f"必須の環境変数が設定されていません: {name}")
    return v.strip()


def _require_int_env(name: str) -> int:
    raw = _require_env(name)
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"環境変数 {name} は整数である必要があります: {raw!r}"
        ) from exc


def _optional_int_env(name: str, *, default: int) -> int:
    raw = _optional_env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(
            f"環境変数 {name} は整数である必要があります: {raw!r}"
        ) from exc


@dataclass(frozen=True)
class Settings:
    service_api_key: str
    database_url: str
    qdrant_host: str
    qdrant_port: int
    qdrant_vector_size: int
    ingest_staging_dir: str
    ingest_allowed_source_root: str | None
    openai_api_key: str
    openai_embedding_model: str
    openai_chat_model: str
    ingest_chunk_size: int
    ingest_chunk_overlap: int

    @staticmethod
    def from_env() -> "Settings":
        service_api_key = _require_env("SERVICE_API_KEY")
        database_url = _require_env("DATABASE_URL")
        qdrant_host = _require_env("QDRANT_HOST")
        qdrant_port = _require_int_env("QDRANT_PORT")
        qdrant_vector_size = _require_int_env("QDRANT_VECTOR_SIZE")
        ingest_staging_dir = _optional_env("INGEST_STAGING_DIR") or str(Path.cwd() / "var" / "ingest_staging")
        ingest_allowed_source_root = _optional_env("INGEST_ALLOWED_SOURCE_ROOT")
        openai_api_key = _require_env("OPENAI_API_KEY")
        openai_embedding_model = _optional_env("OPENAI_EMBEDDING_MODEL") or "text-embedding-3-small"
        openai_chat_model = _optional_env("OPENAI_CHAT_MODEL") or "gpt-5-nano"
        ingest_chunk_size = _optional_int_env("INGEST_CHUNK_SIZE", default=1000)
        ingest_chunk_overlap = _optional_int_env("INGEST_CHUNK_OVERLAP", default=100)
        return Settings(
            service_api_key=service_api_key,
            database_url=database_url,
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            qdrant_vector_size=qdrant_vector_size,
            ingest_staging_dir=ingest_staging_dir,
            ingest_allowed_source_root=ingest_allowed_source_root,
            openai_api_key=openai_api_key,
            openai_embedding_model=openai_embedding_model,
            openai_chat_model=openai_chat_model,
            ingest_chunk_size=ingest_chunk_size,
            ingest_chunk_overlap=ingest_chunk_overlap,
        )

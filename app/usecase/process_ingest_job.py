from __future__ import annotations

import logging
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from domain.chunking.text_chunker import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, split_text_into_chunks
from interface.collection_repository import CollectionRepository, RepositoryError
from interface.embedding_client import EmbeddingClient, EmbeddingClientError
from interface.vector_write_repository import ChunkPoint, VectorWriteRepository

logger = logging.getLogger(__name__)

_UPSERT_BATCH_SIZE = 100


@dataclass(frozen=True)
class ProcessIngestJobResult:
    ingested_chunk_count: int
    ingested_file_count: int


@dataclass(frozen=True)
class ProcessIngestJobUsecase:
    collection_repository: CollectionRepository
    vector_write_repository: VectorWriteRepository
    embedding_client: EmbeddingClient
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP

    def execute(
        self,
        *,
        job_id: str,
        collection_db_id: int,
        qdrant_collection_name: str,
        staged_absolute_paths: tuple[str, ...],
    ) -> ProcessIngestJobResult:
        staging_dir = self._resolve_staging_dir(staged_absolute_paths)
        try:
            return self._process(
                job_id=job_id,
                collection_db_id=collection_db_id,
                qdrant_collection_name=qdrant_collection_name,
                staged_absolute_paths=staged_absolute_paths,
            )
        finally:
            if staging_dir is not None:
                shutil.rmtree(staging_dir, ignore_errors=True)

    def _process(
        self,
        *,
        job_id: str,
        collection_db_id: int,
        qdrant_collection_name: str,
        staged_absolute_paths: tuple[str, ...],
    ) -> ProcessIngestJobResult:
        if not staged_absolute_paths:
            logger.warning("ingest_job_no_files job_id=%s", job_id)
            return ProcessIngestJobResult(ingested_chunk_count=0, ingested_file_count=0)

        try:
            if not self.collection_repository.collection_exists(qdrant_collection_name):
                raise RepositoryError(f"Qdrantコレクションが存在しません: {qdrant_collection_name}")
        except RepositoryError:
            raise
        except Exception as e:
            raise RepositoryError("コレクションの存在確認に失敗しました") from e

        chunk_texts: list[str] = []
        chunk_sources: list[str] = []
        chunk_indices: list[int] = []
        ingested_file_count = 0

        for file_path in staged_absolute_paths:
            path = Path(file_path)
            try:
                raw_text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                raw_text = path.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                logger.exception("ingest_job_read_failed job_id=%s path=%s", job_id, file_path)
                raise

            file_chunks = split_text_into_chunks(
                raw_text,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
            if not file_chunks:
                logger.info("ingest_job_empty_file job_id=%s path=%s", job_id, file_path)
                continue

            ingested_file_count += 1
            for chunk_index, chunk_text in enumerate(file_chunks):
                chunk_texts.append(chunk_text)
                chunk_sources.append(str(path.name))
                chunk_indices.append(chunk_index)

        if not chunk_texts:
            logger.warning("ingest_job_no_chunks job_id=%s", job_id)
            return ProcessIngestJobResult(ingested_chunk_count=0, ingested_file_count=ingested_file_count)

        try:
            vectors = self.embedding_client.embed_texts(chunk_texts)
        except EmbeddingClientError as e:
            logger.exception("ingest_job_embed_failed job_id=%s", job_id)
            raise

        if len(vectors) != len(chunk_texts):
            raise EmbeddingClientError("埋め込み結果の件数が一致しません")

        points = [
            ChunkPoint(
                point_id=str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"{job_id}:{source_path}:{chunk_index}",
                    )
                ),
                vector=vector,
                text=text,
                source_path=source_path,
                chunk_index=chunk_index,
                job_id=job_id,
                collection_db_id=collection_db_id,
            )
            for text, source_path, chunk_index, vector in zip(
                chunk_texts,
                chunk_sources,
                chunk_indices,
                vectors,
                strict=True,
            )
        ]

        for start in range(0, len(points), _UPSERT_BATCH_SIZE):
            batch = points[start : start + _UPSERT_BATCH_SIZE]
            self.vector_write_repository.upsert_chunks(
                collection_name=qdrant_collection_name,
                points=batch,
            )

        logger.info(
            "ingest_job_completed job_id=%s qdrant=%s files=%s chunks=%s",
            job_id,
            qdrant_collection_name,
            ingested_file_count,
            len(points),
        )
        return ProcessIngestJobResult(
            ingested_chunk_count=len(points),
            ingested_file_count=ingested_file_count,
        )

    @staticmethod
    def _resolve_staging_dir(staged_absolute_paths: tuple[str, ...]) -> Path | None:
        if not staged_absolute_paths:
            return None
        return Path(staged_absolute_paths[0]).resolve().parent

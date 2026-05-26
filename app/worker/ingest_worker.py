from __future__ import annotations

import logging

from usecase.process_ingest_job import ProcessIngestJobUsecase

logger = logging.getLogger(__name__)


def run_ingest_job(
    *,
    process_usecase: ProcessIngestJobUsecase,
    job_id: str,
    customer_id: str,
    collection_db_id: int,
    qdrant_collection_name: str,
    staged_absolute_paths: tuple[str, ...],
) -> None:
    """
    受け付け後の非同期処理（チャンク分割・埋め込み・Qdrant 投入）。
    """
    logger.info(
        "ingest_job_started job_id=%s customer_id=%s collection_db_id=%s qdrant=%s files=%s",
        job_id,
        customer_id,
        collection_db_id,
        qdrant_collection_name,
        len(staged_absolute_paths),
    )
    try:
        result = process_usecase.execute(
            job_id=job_id,
            collection_db_id=collection_db_id,
            qdrant_collection_name=qdrant_collection_name,
            staged_absolute_paths=staged_absolute_paths,
        )
    except Exception:
        logger.exception(
            "ingest_job_failed job_id=%s customer_id=%s collection_db_id=%s qdrant=%s",
            job_id,
            customer_id,
            collection_db_id,
            qdrant_collection_name,
        )
        return

    logger.info(
        "ingest_job_finished job_id=%s chunks=%s files=%s",
        job_id,
        result.ingested_chunk_count,
        result.ingested_file_count,
    )

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def run_ingest_job(
    *,
    job_id: str,
    customer_id: str,
    collection_db_id: int,
    qdrant_collection_name: str,
    staged_absolute_paths: tuple[str, ...],
) -> None:
    """
    受け付け後の非同期処理（埋め込み・Qdrant 投入など）。
    現状はプレースホルダー。将来のタスクテーブル連携時もこの関数を拡張する想定。
    """
    logger.info(
        "ingest_job_started job_id=%s customer_id=%s collection_db_id=%s qdrant=%s files=%s",
        job_id,
        customer_id,
        collection_db_id,
        qdrant_collection_name,
        len(staged_absolute_paths),
    )

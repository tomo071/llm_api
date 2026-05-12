from __future__ import annotations

from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse

from domain.errors import DomainValidationError
from usecase.create_collection import CustomerNotFoundError, ExternalServiceError, InvalidApiKeyError
from usecase.ingest_files import (
    CollectionAmbiguousForIngestError,
    CollectionLogicallyDeletedError,
    CollectionNotFoundForIngestError,
    IngestFilesResult,
    IngestFilesUsecase,
)
from worker.ingest_worker import run_ingest_job


def _error_response(*, status_code: int, code: str, message: str, field: str | None = None) -> JSONResponse:
    payload: dict = {"data": {"error": {"code": code, "message": message}}}
    if field is not None:
        payload["data"]["error"]["field"] = field
    return JSONResponse(status_code=status_code, content=payload)


def coerce_file_paths(file_paths: list[str] | str | None) -> list[str]:
    if file_paths is None:
        return []
    if isinstance(file_paths, str):
        return [file_paths]
    return list(file_paths)


def reference_set_error_response(exc: BaseException) -> JSONResponse:
    """ユースケース例外・ドメイン例外から HTTP レスポンスを組み立てる。"""
    if isinstance(exc, InvalidApiKeyError):
        return _error_response(status_code=401, code="invalid_api_key", message="APIキーが一致しません")
    if isinstance(exc, CustomerNotFoundError):
        return _error_response(status_code=404, code="customer_not_found", message=str(exc))
    if isinstance(exc, CollectionNotFoundForIngestError):
        return _error_response(status_code=404, code="collection_not_found", message=str(exc))
    if isinstance(exc, CollectionAmbiguousForIngestError):
        return _error_response(status_code=400, code="collection_ambiguous", message=str(exc))
    if isinstance(exc, CollectionLogicallyDeletedError):
        return _error_response(status_code=409, code="collection_deleted", message=str(exc))
    if isinstance(exc, DomainValidationError):
        return _error_response(
            status_code=400,
            code="validation_error",
            message=str(exc),
            field=getattr(exc, "field", None),
        )
    if isinstance(exc, ExternalServiceError):
        return _error_response(
            status_code=424,
            code="external_service_error",
            message=str(exc) if str(exc) else "外部サービスとの通信に失敗しました",
        )
    raise exc


def reference_set_success_response(result: IngestFilesResult) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "data": {
                "job_id": result.job_id,
                "collection_id": result.collection_db_id,
                "qdrant_collection_name": result.qdrant_collection_name,
                "staged_file_count": len(result.staged_absolute_paths),
            }
        },
    )


def handle_reference_set(
    *,
    usecase: IngestFilesUsecase,
    background_tasks: BackgroundTasks,
    API_key: str,
    customer_id: str,
    use_type: int,
    file_paths: list[str],
) -> JSONResponse:
    paths = coerce_file_paths(file_paths)
    try:
        result = usecase.execute(
            api_key=API_key,
            customer_id=customer_id,
            use_type=use_type,
            file_paths=paths,
        )
    except Exception as e:
        return reference_set_error_response(e)

    background_tasks.add_task(
        run_ingest_job,
        job_id=result.job_id,
        customer_id=result.customer_id,
        collection_db_id=result.collection_db_id,
        qdrant_collection_name=result.qdrant_collection_name,
        staged_absolute_paths=result.staged_absolute_paths,
    )

    return reference_set_success_response(result)

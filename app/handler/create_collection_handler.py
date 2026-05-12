from __future__ import annotations

from fastapi.responses import JSONResponse

from domain.errors import DomainValidationError
from usecase.create_collection import (
    CollectionAlreadyExistsError,
    CreateCollectionResult,
    CreateCollectionUsecase,
    CustomerNotFoundError,
    ExternalServiceError,
    InvalidApiKeyError,
)


def _error_response(*, status_code: int, code: str, message: str, field: str | None = None) -> JSONResponse:
    payload: dict = {"data": {"error": {"code": code, "message": message}}}
    if field is not None:
        payload["data"]["error"]["field"] = field
    return JSONResponse(status_code=status_code, content=payload)


def create_collection_success_response(result: CreateCollectionResult) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "data": {
                "collection_name": result.collection_name,
                "display_name": result.display_name,
                "customer_id": result.customer_id,
            }
        },
    )


def create_collection_error_response(exc: BaseException) -> JSONResponse:
    """ユースケース例外・ドメイン例外から HTTP レスポンスを組み立てる。"""
    if isinstance(exc, InvalidApiKeyError):
        return _error_response(status_code=401, code="invalid_api_key", message="APIキーが一致しません")
    if isinstance(exc, CustomerNotFoundError):
        return _error_response(status_code=404, code="customer_not_found", message=str(exc))
    if isinstance(exc, DomainValidationError):
        return _error_response(status_code=400, code="validation_error", message=str(exc), field=getattr(exc, "field", None))
    if isinstance(exc, CollectionAlreadyExistsError):
        return _error_response(
            status_code=409,
            code="collection_already_exists",
            message=f"コレクションは既に存在します: {exc.collection_name}",
        )
    if isinstance(exc, ExternalServiceError):
        return _error_response(
            status_code=424,
            code="external_service_error",
            message=str(exc) if str(exc) else "外部サービスとの通信に失敗しました",
        )
    raise exc


def create_collection_handler(
    *,
    usecase: CreateCollectionUsecase,
    API_key: str,
    customer_id: str,
    name: str,
) -> JSONResponse:
    try:
        result = usecase.execute(api_key=API_key, customer_id=customer_id, name=name)
    except Exception as e:
        return create_collection_error_response(e)

    return create_collection_success_response(result)

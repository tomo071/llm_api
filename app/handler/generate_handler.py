from __future__ import annotations

from fastapi.responses import JSONResponse

from domain.errors import DomainValidationError
from usecase.create_collection import ExternalServiceError, InvalidApiKeyError
from usecase.generate import (
    GenerateResult,
    GenerateUsecase,
    ReferenceSetDeletedError,
    ReferenceSetNotFoundError,
)


def _error_response(*, status_code: int, code: str, message: str, field: str | None = None) -> JSONResponse:
    payload: dict = {"data": {"error": {"code": code, "message": message}}}
    if field is not None:
        payload["data"]["error"]["field"] = field
    return JSONResponse(status_code=status_code, content=payload)


def generate_success_response(result: GenerateResult) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"data": {"content": result.content}},
    )


def generate_error_response(exc: BaseException) -> JSONResponse:
    if isinstance(exc, InvalidApiKeyError):
        return _error_response(status_code=401, code="invalid_api_key", message="APIキーが一致しません")
    if isinstance(exc, ReferenceSetNotFoundError):
        return _error_response(status_code=404, code="reference_set_not_found", message=str(exc))
    if isinstance(exc, ReferenceSetDeletedError):
        return _error_response(status_code=409, code="reference_set_deleted", message=str(exc))
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


def generate_handler(
    *,
    usecase: GenerateUsecase,
    API_key: str,
    prompt: str,
    reference_set_id: int | None,
) -> JSONResponse:
    try:
        result = usecase.execute(
            api_key=API_key,
            prompt=prompt,
            reference_set_id=reference_set_id,
        )
    except Exception as e:
        return generate_error_response(e)

    return generate_success_response(result)

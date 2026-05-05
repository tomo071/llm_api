from __future__ import annotations

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from domain.errors import DomainValidationError
from usecase.create_collection import (
    CollectionAlreadyExistsError,
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


def build_collections_router(*, usecase: CreateCollectionUsecase) -> APIRouter:
    router = APIRouter()

    @router.post("/collections")
    async def post_collections(
        API_key: str = Form(...),
        customer_id: str = Form(...),
        name: str = Form(...),
    ) -> JSONResponse:
        return await create_collection_handler(
            usecase=usecase,
            API_key=API_key,
            customer_id=customer_id,
            name=name,
        )

    return router


async def create_collection_handler(
    *,
    usecase: CreateCollectionUsecase,
    API_key: str = Form(...),
    customer_id: str = Form(...),
    name: str = Form(...),
) -> JSONResponse:
    try:
        result = usecase.execute(api_key=API_key, customer_id=customer_id, name=name)
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
    except InvalidApiKeyError:
        return _error_response(status_code=401, code="invalid_api_key", message="APIキーが一致しません")
    except CustomerNotFoundError as e:
        return _error_response(status_code=404, code="customer_not_found", message=str(e))
    except DomainValidationError as e:
        return _error_response(status_code=400, code="validation_error", message=str(e), field=getattr(e, "field", None))
    except CollectionAlreadyExistsError as e:
        return _error_response(
            status_code=409,
            code="collection_already_exists",
            message=f"コレクションは既に存在します: {e.collection_name}",
        )
    except ExternalServiceError as e:
        return _error_response(
            status_code=424,
            code="external_service_error",
            message=str(e) if str(e) else "外部サービスとの通信に失敗しました",
        )

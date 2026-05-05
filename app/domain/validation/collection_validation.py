from __future__ import annotations

from domain.errors import DomainValidationError


def require_non_empty(value: str | None, *, field: str) -> str:
    if value is None:
        raise DomainValidationError("この項目は必須です", field=field)
    v = value.strip()
    if not v:
        raise DomainValidationError("空にできません", field=field)
    return v


def validate_collection_inputs(*, api_key: str | None, customer_id: str | None, name: str | None) -> tuple[str, str, str]:
    api_key_v = require_non_empty(api_key, field="API_key")
    customer_id_v = require_non_empty(customer_id, field="customer_id")
    name_v = require_non_empty(name, field="name")
    return api_key_v, customer_id_v, name_v


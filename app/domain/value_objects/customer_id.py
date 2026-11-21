from __future__ import annotations

from dataclasses import dataclass

from domain.errors import DomainValidationError


@dataclass(frozen=True)
class CustomerId:
    value: str

    @staticmethod
    def from_raw(raw: str) -> "CustomerId":
        v = (raw or "").strip()
        if not v:
            raise DomainValidationError("空にできません", field="customer_id")
        return CustomerId(value=v)


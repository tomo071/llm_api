from __future__ import annotations

from dataclasses import dataclass

from domain.errors import DomainValidationError


@dataclass(frozen=True)
class UseType:
    value: int

    @staticmethod
    def from_raw(raw: str | int | None) -> "UseType":
        if raw is None:
            raise DomainValidationError("この項目は必須です", field="use_type")
        if isinstance(raw, int):
            v = raw
        else:
            s = str(raw).strip()
            if not s:
                raise DomainValidationError("空にできません", field="use_type")
            try:
                v = int(s)
            except ValueError as exc:
                raise DomainValidationError("use_type は整数である必要があります", field="use_type") from exc
        if v < 0:
            raise DomainValidationError("use_type は 0 以上の整数である必要があります", field="use_type")
        return UseType(value=v)

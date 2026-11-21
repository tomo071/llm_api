from __future__ import annotations


class DomainError(Exception):
    pass


class DomainValidationError(DomainError):
    def __init__(self, message: str, *, field: str | None = None):
        super().__init__(message)
        self.field = field

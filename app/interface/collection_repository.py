from __future__ import annotations

from typing import Protocol


class RepositoryError(Exception):
    pass


class CollectionRepository(Protocol):
    def collection_exists(self, collection_name: str) -> bool: ...

    def create_collection(self, collection_name: str) -> None: ...


class CustomerRepository(Protocol):
    def customer_exists(self, customer_id: str) -> bool: ...

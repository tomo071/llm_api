from __future__ import annotations

from dataclasses import dataclass

from domain.validation.collection_validation import validate_collection_inputs
from domain.value_objects.collection_name import CollectionDisplayName, QdrantCollectionName
from domain.value_objects.customer_id import CustomerId
from interface.collection_repository import CollectionRepository, CustomerRepository, RepositoryError


class UsecaseError(Exception):
    pass


class InvalidApiKeyError(UsecaseError):
    pass


CUSTOMER_NOT_FOUND_MESSAGE = "指定された顧客IDは登録されていません"


class CustomerNotFoundError(UsecaseError):
    def __init__(self, message: str = CUSTOMER_NOT_FOUND_MESSAGE) -> None:
        super().__init__(message)


class CollectionAlreadyExistsError(UsecaseError):
    def __init__(self, collection_name: str):
        super().__init__("コレクションは既に存在します")
        self.collection_name = collection_name


class ExternalServiceError(UsecaseError):
    pass


@dataclass(frozen=True)
class CreateCollectionResult:
    collection_name: str
    display_name: str
    customer_id: str


@dataclass(frozen=True)
class CreateCollectionUsecase:
    repository: CollectionRepository
    customer_repository: CustomerRepository
    service_api_key: str

    def execute(self, *, api_key: str | None, customer_id: str | None, name: str | None) -> CreateCollectionResult:
        api_key_v, customer_id_v, name_v = validate_collection_inputs(
            api_key=api_key,
            customer_id=customer_id,
            name=name,
        )

        if api_key_v != self.service_api_key:
            raise InvalidApiKeyError("APIキーが無効です")

        cid = CustomerId.from_raw(customer_id_v)
        try:
            if not self.customer_repository.customer_exists(cid.value):
                raise CustomerNotFoundError()
        except CustomerNotFoundError:
            raise
        except Exception as e:
            raise ExternalServiceError("顧客情報の確認に失敗しました") from e
        display = CollectionDisplayName.from_raw(name_v)
        qdrant_name = QdrantCollectionName.from_parts(customer_id=cid.value, display_name=display.value)

        try:
            exists = self.repository.collection_exists(qdrant_name.value)
        except RepositoryError as e:
            raise ExternalServiceError("リポジトリの操作に失敗しました") from e

        if exists:
            raise CollectionAlreadyExistsError(qdrant_name.value)

        try:
            self.repository.create_collection(qdrant_name.value)
        except RepositoryError as e:
            raise ExternalServiceError("リポジトリの操作に失敗しました") from e

        return CreateCollectionResult(
            collection_name=qdrant_name.value,
            display_name=display.value,
            customer_id=cid.value,
        )


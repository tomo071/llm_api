from __future__ import annotations

from dataclasses import dataclass

from domain.validation.collection_validation import validate_collection_inputs
from domain.value_objects.collection_name import CollectionDisplayName, QdrantCollectionName
from domain.value_objects.customer_id import CustomerId
from domain.value_objects.use_type import UseType
from interface.collection_catalog_repository import CollectionCatalogRepository
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


class CatalogCollectionAlreadyExistsError(UsecaseError):
    """同一 customer_id / use_type の MySQL コレクションが既に存在する。"""


class ExternalServiceError(UsecaseError):
    pass


@dataclass(frozen=True)
class CreateCollectionResult:
    collection_name: str
    display_name: str
    customer_id: str
    collection_id: int
    use_type: int


@dataclass(frozen=True)
class CreateCollectionUsecase:
    repository: CollectionRepository
    customer_repository: CustomerRepository
    collection_catalog_repository: CollectionCatalogRepository
    service_api_key: str

    def execute(
        self,
        *,
        api_key: str | None,
        customer_id: str | None,
        name: str | None,
        use_type: str | int | None,
    ) -> CreateCollectionResult:
        api_key_v, customer_id_v, name_v = validate_collection_inputs(
            api_key=api_key,
            customer_id=customer_id,
            name=name,
        )

        if api_key_v != self.service_api_key:
            raise InvalidApiKeyError("APIキーが無効です")

        use_type_v = UseType.from_raw(use_type)
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
            catalog_lookup = self.collection_catalog_repository.find_for_ingest(
                customer_id=cid.value,
                use_type=use_type_v.value,
            )
        except Exception as e:
            raise ExternalServiceError("コレクション情報の確認に失敗しました") from e

        if catalog_lookup.status == "active":
            raise CatalogCollectionAlreadyExistsError(
                "同一の customer_id と use_type のコレクションが既に登録されています"
            )
        if catalog_lookup.status == "ambiguous":
            raise CatalogCollectionAlreadyExistsError(
                "同一の customer_id と use_type に複数のコレクションが存在します"
            )

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

        try:
            catalog_result = self.collection_catalog_repository.create_active_collection(
                customer_id=cid.value,
                collection_name=display.value,
                use_type=use_type_v.value,
            )
        except Exception as e:
            raise ExternalServiceError("コレクション情報の登録に失敗しました") from e

        if catalog_result.status == "customer_not_found":
            raise CustomerNotFoundError()
        if catalog_result.status == "duplicate":
            raise CatalogCollectionAlreadyExistsError(
                "同一の customer_id と use_type のコレクションが既に登録されています"
            )
        if catalog_result.collection is None:
            raise ExternalServiceError("コレクション情報の登録に失敗しました")

        return CreateCollectionResult(
            collection_name=qdrant_name.value,
            display_name=display.value,
            customer_id=cid.value,
            collection_id=catalog_result.collection.id,
            use_type=catalog_result.collection.use_type,
        )


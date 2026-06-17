from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from domain.errors import DomainValidationError
from domain.validation.collection_validation import require_non_empty
from domain.validation.ingestion_validation import IngestionFileSpec, validate_ingestion_file_specs
from domain.value_objects.collection_name import CollectionDisplayName, QdrantCollectionName
from domain.value_objects.customer_id import CustomerId
from domain.value_objects.use_type import UseType
from interface.collection_catalog_repository import CollectionCatalogRepository
from interface.collection_repository import CustomerRepository
from usecase.create_collection import (
    CustomerNotFoundError,
    ExternalServiceError,
    InvalidApiKeyError,
    UsecaseError,
)


class CollectionNotFoundForIngestError(UsecaseError):
    """指定の customer_id / use_type に該当する collection がない。"""


class CollectionAmbiguousForIngestError(UsecaseError):
    """同一条件に複数の collection が存在する。"""


class CollectionLogicallyDeletedError(UsecaseError):
    """collection が論理削除済み。"""


@dataclass(frozen=True)
class IngestFilesResult:
    job_id: str
    customer_id: str
    collection_db_id: int
    qdrant_collection_name: str
    staged_absolute_paths: tuple[str, ...]


@dataclass(frozen=True)
class IngestFilesUsecase:
    customer_repository: CustomerRepository
    collection_catalog_repository: CollectionCatalogRepository
    service_api_key: str
    ingest_staging_dir: Path
    ingest_allowed_source_root: Path | None

    def execute(
        self,
        *,
        api_key: str | None,
        customer_id: str | None,
        use_type: str | int | None,
        file_paths: list[str],
    ) -> IngestFilesResult:
        api_key_v = require_non_empty(api_key, field="API_key")
        customer_id_v = require_non_empty(customer_id, field="customer_id")
        use_type_v = UseType.from_raw(use_type)

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

        try:
            lookup = self.collection_catalog_repository.find_for_ingest(
                customer_id=cid.value,
                use_type=use_type_v.value,
            )
        except Exception as e:
            raise ExternalServiceError("コレクション情報の取得に失敗しました") from e

        if lookup.status == "not_found":
            raise CollectionNotFoundForIngestError("指定されたコレクションが見つかりません")
        if lookup.status == "ambiguous":
            raise CollectionAmbiguousForIngestError("同一条件に複数のコレクションが存在します")
        if lookup.status == "deleted":
            raise CollectionLogicallyDeletedError("コレクションは論理削除されています")
        if lookup.collection is None:
            raise ExternalServiceError("コレクション情報の取得に失敗しました")

        normalized_paths = self._normalize_and_require_paths(file_paths)
        specs = self._build_file_specs(normalized_paths)
        validate_ingestion_file_specs(specs)

        display = CollectionDisplayName.from_raw(lookup.collection.collection_name)
        qdrant_name = QdrantCollectionName.from_parts(customer_id=cid.value, display_name=display.value)

        job_id = str(uuid.uuid4())
        staging_root = self.ingest_staging_dir.resolve()
        staging_root.mkdir(parents=True, exist_ok=True)
        job_dir = staging_root / job_id

        try:
            job_dir.mkdir(parents=False, exist_ok=False)
            staged_paths: list[str] = []
            for i, src in enumerate(normalized_paths):
                resolved_src = Path(src).expanduser().resolve()
                dest = job_dir / f"{i:03d}_{resolved_src.name}"
                shutil.copy2(resolved_src, dest)
                staged_paths.append(str(dest.resolve()))
        except OSError as e:
            shutil.rmtree(job_dir, ignore_errors=True)
            raise ExternalServiceError("ファイルの保存に失敗しました") from e
        except Exception:
            shutil.rmtree(job_dir, ignore_errors=True)
            raise

        return IngestFilesResult(
            job_id=job_id,
            customer_id=cid.value,
            collection_db_id=lookup.collection.id,
            qdrant_collection_name=qdrant_name.value,
            staged_absolute_paths=tuple(staged_paths),
        )

    def _normalize_and_require_paths(self, file_paths: list[str]) -> list[str]:
        out: list[str] = []
        for raw in file_paths:
            v = (raw or "").strip()
            if not v:
                continue
            out.append(v)
        if not out:
            raise DomainValidationError("少なくとも1つのファイルパスが必要です", field="file_paths")
        return out

    def _build_file_specs(self, paths: list[str]) -> list[IngestionFileSpec]:
        specs: list[IngestionFileSpec] = []
        allowed_root = self.ingest_allowed_source_root.resolve() if self.ingest_allowed_source_root else None

        for p in paths:
            path_obj = Path(p).expanduser()
            try:
                resolved = path_obj.resolve()
            except OSError as e:
                raise DomainValidationError(f"パスを解決できません: {p}", field="file_paths") from e

            if allowed_root is not None:
                try:
                    resolved.relative_to(allowed_root)
                except ValueError:
                    raise DomainValidationError(
                        f"許可されたルート外のパスです: {p}",
                        field="file_paths",
                    )

            if not resolved.is_file():
                raise DomainValidationError(f"ファイルが存在しません: {p}", field="file_paths")

            try:
                size = resolved.stat().st_size
            except OSError as e:
                raise DomainValidationError(f"ファイルを読み取れません: {p}", field="file_paths") from e

            specs.append(IngestionFileSpec(path=str(resolved), size_bytes=int(size)))

        return specs

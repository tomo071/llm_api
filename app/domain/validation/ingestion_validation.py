from __future__ import annotations

from dataclasses import dataclass
import os

from domain.errors import DomainValidationError

MAX_INGEST_FILES = 5
MAX_TOTAL_BYTES = 20 * 1024 * 1024

# テキスト系として扱う拡張子（小文字で比較）
ALLOWED_TEXT_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".txt",
        ".text",
        ".md",
        ".markdown",
        ".csv",
        ".tsv",
        ".json",
        ".xml",
        ".log",
        ".yaml",
        ".yml",
        ".htm",
        ".html",
        ".rst",
    }
)


@dataclass(frozen=True)
class IngestionFileSpec:
    """検証対象の1ファイル（パス文字列と事前取得済みのサイズ）。"""

    path: str
    size_bytes: int


def validate_ingestion_file_specs(specs: list[IngestionFileSpec]) -> None:
    if not specs:
        raise DomainValidationError("少なくとも1つのファイルパスが必要です", field="file_paths")
    if len(specs) > MAX_INGEST_FILES:
        raise DomainValidationError(
            f"ファイルは最大{MAX_INGEST_FILES}件までです",
            field="file_paths",
        )
    total = sum(s.size_bytes for s in specs)
    if total > MAX_TOTAL_BYTES:
        raise DomainValidationError(
            f"ファイル合計サイズは{MAX_TOTAL_BYTES // (1024 * 1024)}MB以下である必要があります",
            field="file_paths",
        )
    for spec in specs:
        if spec.size_bytes < 0:
            raise DomainValidationError("ファイルサイズが不正です", field="file_paths")
        _, ext = os.path.splitext(spec.path)
        if ext.lower() not in ALLOWED_TEXT_EXTENSIONS:
            raise DomainValidationError(
                f"許可されていない拡張子です: {ext or '(なし)'}",
                field="file_paths",
            )

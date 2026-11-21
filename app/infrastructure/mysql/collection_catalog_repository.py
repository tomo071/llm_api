from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine, text

from interface.collection_catalog_repository import (
    ActiveCollectionRecord,
    CollectionCatalogRepository,
    IngestCollectionLookup,
)


@dataclass(frozen=True)
class MysqlCollectionCatalogRepository(CollectionCatalogRepository):
    engine: Engine

    def find_for_ingest(self, *, customer_id: str, use_type: int) -> IngestCollectionLookup:
        stmt = text(
            """
            SELECT c.id, c.collection_name, c.delete_flag
            FROM collection c
            INNER JOIN customer cu
              ON cu.id = c.customer_id
             AND cu.delete_flag = FALSE
             AND cu.deleted_at IS NULL
            WHERE cu.customer_id = :cid
              AND c.use_type = :ut
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(stmt, {"cid": customer_id, "ut": use_type}).fetchall()

        if len(rows) == 0:
            return IngestCollectionLookup(status="not_found", collection=None)
        if len(rows) > 1:
            return IngestCollectionLookup(status="ambiguous", collection=None)

        row = rows[0]
        cid = int(row[0])
        name = str(row[1])
        delete_flag = bool(row[2])
        if delete_flag:
            return IngestCollectionLookup(status="deleted", collection=None)
        return IngestCollectionLookup(
            status="active",
            collection=ActiveCollectionRecord(id=cid, collection_name=name),
        )

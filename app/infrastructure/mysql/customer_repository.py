from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Engine, text

from interface.collection_repository import CustomerRepository


@dataclass(frozen=True)
class MysqlCustomerRepository(CustomerRepository):
    """customer テーブルの文字列カラム customer_id で存在確認する。"""

    engine: Engine

    def customer_exists(self, customer_id: str) -> bool:
        stmt = text(
            """
            SELECT 1
            FROM customer
            WHERE customer_id = :cid
              AND delete_flag = FALSE
              AND deleted_at IS NULL
            LIMIT 1
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(stmt, {"cid": customer_id}).fetchone()
            return row is not None

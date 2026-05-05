from __future__ import annotations

from fastapi import FastAPI
from qdrant_client import QdrantClient
from sqlalchemy import create_engine

from handler.create_collection_handler import build_collections_router
from infrastructure.mysql.customer_repository import MysqlCustomerRepository
from infrastructure.qdrant.collection_repository import QdrantCollectionRepository
from infrastructure.settings import Settings
from usecase.create_collection import CreateCollectionUsecase


def create_app() -> FastAPI:
    settings = Settings.from_env()

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    customer_repo = MysqlCustomerRepository(engine=engine)

    qdrant_client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    collection_repo = QdrantCollectionRepository(client=qdrant_client, vector_size=settings.qdrant_vector_size)
    create_collection_usecase = CreateCollectionUsecase(
        repository=collection_repo,
        customer_repository=customer_repo,
        service_api_key=settings.service_api_key,
    )

    app = FastAPI()

    @app.get("/collections")
    def read_root():
        return {"message": "ready"}

    app.include_router(build_collections_router(usecase=create_collection_usecase))

    return app


app = create_app()

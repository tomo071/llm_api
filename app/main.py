from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form
from qdrant_client import QdrantClient
from sqlalchemy import create_engine

from handler.create_collection_handler import create_collection_handler
from handler.ingest_files_handler import handle_reference_set
from infrastructure.mysql.collection_catalog_repository import MysqlCollectionCatalogRepository
from infrastructure.mysql.customer_repository import MysqlCustomerRepository
from infrastructure.qdrant.collection_repository import QdrantCollectionRepository
from infrastructure.settings import Settings
from usecase.create_collection import CreateCollectionUsecase
from usecase.ingest_files import IngestFilesUsecase


def create_app() -> FastAPI:
    settings = Settings.from_env()

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    customer_repo = MysqlCustomerRepository(engine=engine)
    collection_catalog_repo = MysqlCollectionCatalogRepository(engine=engine)

    qdrant_client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    collection_repo = QdrantCollectionRepository(client=qdrant_client, vector_size=settings.qdrant_vector_size)
    create_collection_usecase = CreateCollectionUsecase(
        repository=collection_repo,
        customer_repository=customer_repo,
        service_api_key=settings.service_api_key,
    )
    ingest_usecase = IngestFilesUsecase(
        customer_repository=customer_repo,
        collection_catalog_repository=collection_catalog_repo,
        service_api_key=settings.service_api_key,
        ingest_staging_dir=Path(settings.ingest_staging_dir),
        ingest_allowed_source_root=Path(settings.ingest_allowed_source_root).resolve()
        if settings.ingest_allowed_source_root
        else None,
    )

    app = FastAPI()

    @app.get("/collections")
    def read_root():
        return {"message": "ready"}

    @app.post("/collections")
    async def post_collections(
        API_key: str = Form(...),
        customer_id: str = Form(...),
        name: str = Form(...),
    ):
        return create_collection_handler(
            usecase=create_collection_usecase,
            API_key=API_key,
            customer_id=customer_id,
            name=name,
        )

    @app.post("/reference_set")
    async def post_reference_set(
        background_tasks: BackgroundTasks,
        API_key: str = Form(...),
        customer_id: str = Form(...),
        use_type: int = Form(...),
        file_paths: list[str] = Form(default_factory=list),
    ):
        return handle_reference_set(
            usecase=ingest_usecase,
            background_tasks=background_tasks,
            API_key=API_key,
            customer_id=customer_id,
            use_type=use_type,
            file_paths=file_paths,
        )

    return app


app = create_app()

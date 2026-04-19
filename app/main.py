from fastapi import FastAPI
import pymysql
from qdrant_client import QdrantClient

app = FastAPI()

@app.get("/")
def read_root():
    # 簡易的な接続確認
    return {"message": "FastAPI, MySQL, and Qdrant are ready!"}

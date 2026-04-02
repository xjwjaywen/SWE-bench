from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import ATTACHMENTS_DIR
from app.database import init_db
from app.routers import chat, conversations, memory
from app.services.indexer import build_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    build_index()
    yield


app = FastAPI(title="Email Search API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(memory.router)

# 附件文件静态服务
if ATTACHMENTS_DIR.exists():
    app.mount("/api/attachments", StaticFiles(directory=str(ATTACHMENTS_DIR)), name="attachments")


@app.get("/api/health")
async def health():
    return {"status": "ok"}

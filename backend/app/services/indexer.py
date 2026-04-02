"""邮件索引服务：将邮件内容向量化并存入 ChromaDB。"""

import chromadb

from app.config import CHROMA_DIR, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL
from app.utils.email_loader import get_email_text, load_emails

COLLECTION_NAME = "emails"

_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_index(force: bool = False) -> int:
    """对所有邮件建立向量索引。返回索引的文档数量。"""
    collection = get_collection()

    if not force and collection.count() > 0:
        return collection.count()

    emails = load_emails()
    if not emails:
        return 0

    # 清空旧数据
    if collection.count() > 0:
        client = get_chroma_client()
        client.delete_collection(COLLECTION_NAME)
        collection = get_collection()

    ids = []
    documents = []
    metadatas = []

    for email in emails:
        text = get_email_text(email)
        # ChromaDB 有文档长度限制，截断过长内容
        if len(text) > 8000:
            text = text[:8000]

        ids.append(email["id"])
        documents.append(text)
        metadatas.append({
            "email_id": email["id"],
            "subject": email["subject"],
            "from_name": email["from"]["name"],
            "from_email": email["from"]["email"],
            "date": email["date"],
            "tags": ", ".join(email.get("tags", [])),
            "attachments": ", ".join(a["filename"] for a in email.get("attachments", [])),
        })

    # 分批插入（ChromaDB 单次限制）
    batch_size = 40
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )

    return collection.count()

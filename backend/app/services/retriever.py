"""检索服务：语义检索最相关的邮件片段。"""

from app.config import RETRIEVAL_TOP_K
from app.services.indexer import get_collection


def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    """根据用户问题检索最相关的邮件。

    返回列表，每项包含:
    - email_id, subject, from_name, from_email, date, tags, attachments
    - document: 匹配到的邮件全文
    - distance: 相似度距离（越小越相似）
    """
    top_k = top_k or RETRIEVAL_TOP_K
    collection = get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
    )

    sources = []
    for i in range(len(results["ids"][0])):
        metadata = results["metadatas"][0][i]
        sources.append({
            "email_id": metadata["email_id"],
            "subject": metadata["subject"],
            "from_name": metadata["from_name"],
            "from_email": metadata["from_email"],
            "date": metadata["date"],
            "tags": metadata.get("tags", ""),
            "attachments": metadata.get("attachments", ""),
            "document": results["documents"][0][i],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })

    return sources

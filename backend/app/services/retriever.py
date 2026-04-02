"""检索服务：语义检索 + 关键词匹配混合检索。"""

import re

from app.config import RETRIEVAL_TOP_K
from app.services.indexer import get_collection


def _extract_keywords(query: str) -> list[str]:
    """从查询中提取有意义的关键词（≥2字符）。"""
    # 去掉常见停用词
    stop_words = {"的", "了", "吗", "呢", "是", "有", "在", "被", "把", "和", "与",
                  "还", "也", "都", "就", "会", "能", "要", "可以", "什么", "怎么",
                  "哪些", "多少", "如何", "是否", "关于", "最近", "目前"}
    # 中文按字切分不太好，按常见分隔拆
    words = re.split(r"[，。？！\s,.\?!、]+", query)
    keywords = []
    for w in words:
        w = w.strip()
        if len(w) >= 2 and w not in stop_words:
            keywords.append(w)
    return keywords


def _keyword_search(keywords: list[str], top_k: int) -> list[dict]:
    """使用 ChromaDB 的 where_document 进行关键词匹配。"""
    collection = get_collection()
    if collection.count() == 0 or not keywords:
        return []

    # 用 $or + $contains 做多关键词搜索
    where_conditions = [{"$contains": kw} for kw in keywords[:5]]

    try:
        if len(where_conditions) == 1:
            where_doc = where_conditions[0]
        else:
            where_doc = {"$or": where_conditions}

        results = collection.get(
            where_document=where_doc,
            include=["documents", "metadatas"],
            limit=top_k,
        )

        sources = []
        for i in range(len(results["ids"])):
            metadata = results["metadatas"][i]
            sources.append({
                "email_id": metadata["email_id"],
                "subject": metadata["subject"],
                "from_name": metadata["from_name"],
                "from_email": metadata["from_email"],
                "date": metadata["date"],
                "tags": metadata.get("tags", ""),
                "attachments": metadata.get("attachments", ""),
                "document": results["documents"][i],
                "distance": 0.5,  # 关键词匹配给一个中等距离
            })
        return sources
    except Exception:
        return []


def _semantic_search(query: str, top_k: int) -> list[dict]:
    """使用 ChromaDB 的向量检索。"""
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


def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    """混合检索：关键词匹配 + 语义检索，去重合并。"""
    top_k = top_k or RETRIEVAL_TOP_K

    # 1. 关键词检索
    keywords = _extract_keywords(query)
    keyword_results = _keyword_search(keywords, top_k)

    # 2. 语义检索
    semantic_results = _semantic_search(query, top_k)

    # 3. 合并去重，关键词匹配的排在前面
    seen_ids = set()
    merged = []

    # 先放关键词匹配的结果
    for r in keyword_results:
        if r["email_id"] not in seen_ids:
            seen_ids.add(r["email_id"])
            merged.append(r)

    # 再放语义检索的结果
    for r in semantic_results:
        if r["email_id"] not in seen_ids:
            seen_ids.add(r["email_id"])
            merged.append(r)

    return merged[:top_k]

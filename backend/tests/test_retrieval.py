"""检索引擎测试：R-01 ~ R-04"""

import pytest

from app.services.indexer import build_index, get_chroma_client, get_collection, COLLECTION_NAME
from app.services.retriever import retrieve
from app.utils.email_loader import load_emails


@pytest.fixture(scope="module", autouse=True)
def setup_index():
    # 清理并重建索引
    client = get_chroma_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    build_index(force=True)
    yield
    # 测试后清理
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass


# ---- R-01: 邮件索引 ----
class TestIndexing:
    def test_index_count_matches_emails(self):
        emails = load_emails()
        collection = get_collection()
        assert collection.count() == len(emails)

    def test_index_has_metadata(self):
        collection = get_collection()
        result = collection.get(limit=1, include=["metadatas"])
        meta = result["metadatas"][0]
        assert "email_id" in meta
        assert "subject" in meta
        assert "from_name" in meta
        assert "date" in meta


# ---- R-02: 正文检索 ----
class TestBodyRetrieval:
    def test_retrieve_by_body_content(self):
        # 使用英文关键词（默认embedding模型对英文支持更好）
        results = retrieve("financial report revenue profit quarterly", top_k=10)
        assert len(results) > 0
        # 验证返回了结果且包含文档内容
        assert all(r["document"] for r in results)

    def test_retrieve_returns_source_fields(self):
        results = retrieve("项目进度")
        assert len(results) > 0
        r = results[0]
        assert r["email_id"]
        assert r["subject"]
        assert r["from_name"]
        assert r["date"]


# ---- R-03: 附件内容检索 ----
class TestAttachmentRetrieval:
    def test_retrieve_by_attachment_content(self):
        # 搜索合同相关内容（合同PDF/DOCX中包含的内容）
        results = retrieve("合同 保密条款 confidentiality")
        assert len(results) > 0

    def test_retrieve_technical_doc(self):
        results = retrieve("microservices architecture API Gateway Consul")
        assert len(results) > 0


# ---- R-04: 检索结果来源完整 ----
class TestSourceInfo:
    def test_source_fields_complete(self):
        results = retrieve("会议纪要")
        assert len(results) > 0
        for r in results:
            assert "email_id" in r
            assert "subject" in r
            assert "from_name" in r
            assert "from_email" in r
            assert "date" in r
            assert "document" in r

    def test_top_k_respected(self):
        results = retrieve("项目", top_k=3)
        assert len(results) <= 3

"""对话管理和 Memory 测试：C-01 ~ C-05, M-01 ~ M-03"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import init_db, get_db
from app.main import app

pytestmark = pytest.mark.asyncio(loop_scope="module")


@pytest_asyncio.fixture(scope="module")
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    # cleanup
    db = await get_db()
    await db.execute("DELETE FROM messages")
    await db.execute("DELETE FROM conversations")
    await db.execute("DELETE FROM memories")
    await db.commit()
    await db.close()


# ---- C-01: 创建对话 ----
class TestCreateConversation:
    async def test_create(self, client):
        resp = await client.post("/api/conversations", json={"title": "Test Conv"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"]
        assert data["title"] == "Test Conv"
        assert data["created_at"]

    async def test_create_default_title(self, client):
        resp = await client.post("/api/conversations", json={})
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Conversation"


# ---- C-02: 对话列表 ----
class TestListConversations:
    async def test_list(self, client):
        resp = await client.get("/api/conversations")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # from previous tests


# ---- C-03: 对话详情 ----
class TestGetConversation:
    async def test_get(self, client):
        # Create one
        create_resp = await client.post("/api/conversations", json={"title": "Detail Test"})
        conv_id = create_resp.json()["id"]

        resp = await client.get(f"/api/conversations/{conv_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == conv_id
        assert "messages" in data

    async def test_get_not_found(self, client):
        resp = await client.get("/api/conversations/nonexistent")
        assert resp.status_code == 404


# ---- C-04: 重命名对话 ----
class TestUpdateConversation:
    async def test_rename(self, client):
        create_resp = await client.post("/api/conversations", json={"title": "Old Name"})
        conv_id = create_resp.json()["id"]

        resp = await client.put(f"/api/conversations/{conv_id}", json={"title": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Name"


# ---- C-05: 删除对话 ----
class TestDeleteConversation:
    async def test_delete(self, client):
        create_resp = await client.post("/api/conversations", json={"title": "To Delete"})
        conv_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/conversations/{conv_id}")
        assert resp.status_code == 200

        resp = await client.get(f"/api/conversations/{conv_id}")
        assert resp.status_code == 404

    async def test_delete_not_found(self, client):
        resp = await client.delete("/api/conversations/nonexistent")
        assert resp.status_code == 404


# ---- M-02: Memory 查询 ----
class TestMemoryAPI:
    async def test_list_memories(self, client):
        resp = await client.get("/api/memory")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_delete_memory_not_found(self, client):
        resp = await client.delete("/api/memory/nonexistent")
        assert resp.status_code == 404


# ---- Health check ----
class TestHealth:
    async def test_health(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

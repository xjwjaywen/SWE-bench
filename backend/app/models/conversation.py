"""对话和消息的 Pydantic 模型。"""

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class ConversationUpdate(BaseModel):
    title: str


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageSource(BaseModel):
    email_id: str
    subject: str
    from_: str  # "from" is reserved
    from_email: str = ""
    date: str
    attachments: list[str] = []
    snippet: str = ""

    class Config:
        populate_by_name = True


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: list[MessageSource] = []
    created_at: str


class MessageCreate(BaseModel):
    content: str


class ChatResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut

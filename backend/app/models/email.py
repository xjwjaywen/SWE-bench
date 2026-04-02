"""邮件数据的 Pydantic 模型。"""

from pydantic import BaseModel


class EmailPerson(BaseModel):
    name: str
    email: str


class EmailAttachment(BaseModel):
    filename: str
    type: str


class EmailOut(BaseModel):
    id: str
    from_: EmailPerson
    to: list[EmailPerson]
    cc: list[EmailPerson] = []
    subject: str
    body: str
    date: str
    tags: list[str] = []
    attachments: list[EmailAttachment] = []

    class Config:
        populate_by_name = True

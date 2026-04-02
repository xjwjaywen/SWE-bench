"""加载邮件 JSON 数据和解析附件内容。"""

import json
from pathlib import Path

from app.config import ATTACHMENTS_DIR, EMAILS_DIR
from app.utils.file_parser import parse_file


def load_emails() -> list[dict]:
    emails_file = EMAILS_DIR / "emails.json"
    with open(emails_file, encoding="utf-8") as f:
        return json.load(f)


def get_email_text(email: dict) -> str:
    """将邮件元数据 + 正文 + 附件内容合并为一段可索引文本。"""
    parts = [
        f"Subject: {email['subject']}",
        f"From: {email['from']['name']} <{email['from']['email']}>",
        f"To: {', '.join(r['name'] + ' <' + r['email'] + '>' for r in email['to'])}",
        f"Date: {email['date']}",
        f"Tags: {', '.join(email.get('tags', []))}",
        "",
        email["body"],
    ]

    for att in email.get("attachments", []):
        filepath = str(ATTACHMENTS_DIR / att["filename"])
        content = parse_file(filepath)
        if content:
            parts.append(f"\n[Attachment: {att['filename']}]\n{content}")

    return "\n".join(parts)

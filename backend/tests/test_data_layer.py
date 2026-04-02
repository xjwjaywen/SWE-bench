"""数据层测试：D-01 ~ D-04, P-01 ~ P-06"""

import json
from pathlib import Path

import pytest

from app.config import ATTACHMENTS_DIR, EMAILS_DIR
from app.utils.file_parser import parse_file

EMAILS_FILE = EMAILS_DIR / "emails.json"

REQUIRED_EXTENSIONS = {"pdf", "docx", "xlsx", "pptx", "txt", "csv", "png", "jpg", "zip"}


@pytest.fixture(scope="module")
def emails():
    with open(EMAILS_FILE, encoding="utf-8") as f:
        return json.load(f)


# ---- D-01: 假数据完整性 ----
class TestDataIntegrity:
    def test_email_count(self, emails):
        assert len(emails) == 100

    def test_required_fields(self, emails):
        required = {"id", "from", "to", "subject", "body", "date", "tags", "attachments"}
        for email in emails:
            missing = required - set(email.keys())
            assert not missing, f"{email['id']} missing fields: {missing}"

    def test_fields_non_empty(self, emails):
        for email in emails:
            assert email["id"], "id is empty"
            assert email["from"]["email"], f"{email['id']}: from.email is empty"
            assert email["subject"], f"{email['id']}: subject is empty"
            assert email["body"], f"{email['id']}: body is empty"
            assert email["date"], f"{email['id']}: date is empty"

    def test_unique_ids(self, emails):
        ids = [e["id"] for e in emails]
        assert len(ids) == len(set(ids)), "Duplicate email IDs found"


# ---- D-02: 附件文件存在 ----
class TestAttachmentFiles:
    def test_all_attachments_exist(self, emails):
        for email in emails:
            for att in email["attachments"]:
                filepath = ATTACHMENTS_DIR / att["filename"]
                assert filepath.exists(), f"Missing: {filepath}"

    def test_attachments_non_empty(self, emails):
        for email in emails:
            for att in email["attachments"]:
                filepath = ATTACHMENTS_DIR / att["filename"]
                assert filepath.stat().st_size > 0, f"Empty file: {filepath}"


# ---- D-03: 附件格式覆盖 ----
class TestAttachmentCoverage:
    def test_all_formats_present(self, emails):
        found = set()
        for email in emails:
            for att in email["attachments"]:
                found.add(att["type"])
        missing = REQUIRED_EXTENSIONS - found
        assert not missing, f"Missing attachment types: {missing}"


# ---- D-04: 附件可解析 ----
class TestAttachmentParsing:
    def test_parseable_attachments(self, emails):
        parsed_count = 0
        for email in emails:
            for att in email["attachments"]:
                filepath = str(ATTACHMENTS_DIR / att["filename"])
                result = parse_file(filepath)
                assert result, f"Failed to parse: {att['filename']}"
                parsed_count += 1
        assert parsed_count > 0


# ---- P-01 ~ P-06: 各格式解析测试 ----
class TestFileParser:
    def _find_file(self, emails, ext: str) -> str:
        for email in emails:
            for att in email["attachments"]:
                if att["type"] == ext:
                    return str(ATTACHMENTS_DIR / att["filename"])
        pytest.skip(f"No .{ext} file found")

    def test_parse_pdf(self, emails):
        result = parse_file(self._find_file(emails, "pdf"))
        assert len(result) > 10

    def test_parse_docx(self, emails):
        result = parse_file(self._find_file(emails, "docx"))
        assert len(result) > 10

    def test_parse_xlsx(self, emails):
        result = parse_file(self._find_file(emails, "xlsx"))
        assert len(result) > 10

    def test_parse_pptx(self, emails):
        result = parse_file(self._find_file(emails, "pptx"))
        assert len(result) > 10

    def test_parse_csv(self, emails):
        result = parse_file(self._find_file(emails, "csv"))
        assert len(result) > 10

    def test_parse_txt(self, emails):
        result = parse_file(self._find_file(emails, "txt"))
        assert len(result) > 10

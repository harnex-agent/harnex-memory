from harnex_memory.core.documents import (
    build_document_content,
    list_document_statuses,
    read_document,
)
from harnex_memory.core.models import DocumentKind


def test_list_document_statuses_uses_default_paths(tmp_path):
    statuses = list_document_statuses(tmp_path)

    assert [status.kind for status in statuses] == [
        DocumentKind.SKILL,
        DocumentKind.RULE,
        DocumentKind.HOOK,
    ]
    assert statuses[0].path.endswith(".harnex/memory/skills.md")


def test_read_document_returns_template_when_missing(tmp_path):
    assert read_document(tmp_path, DocumentKind.RULE) == "# Rules\n\n"


def test_build_document_content_appends_once(tmp_path):
    addition = "## 새 규칙\n\n- 같은 내용은 한 번만 추가한다."

    first = build_document_content(tmp_path, DocumentKind.RULE, addition)
    (tmp_path / ".harnex/memory").mkdir(parents=True)
    (tmp_path / ".harnex/memory/rules.md").write_text(first, encoding="utf-8")
    second = build_document_content(tmp_path, DocumentKind.RULE, addition)

    assert second.count("## 새 규칙") == 1

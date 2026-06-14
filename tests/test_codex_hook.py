from pathlib import Path

from harnex_memory.core.codex_hook import (
    extract_metadata,
    extract_project_root,
    extract_prompt,
    parse_hook_payload,
)


def test_parse_hook_payload_accepts_json_prompt(tmp_path: Path) -> None:
    payload = parse_hook_payload(
        f'{{"hook_event_name":"UserPromptSubmit","prompt":"항상 한국어로 답변","cwd":"{tmp_path}"}}'
    )

    assert extract_prompt(payload) == "항상 한국어로 답변"
    assert extract_project_root(payload, fallback=Path("/tmp")).resolve() == tmp_path.resolve()
    assert extract_metadata(payload)["hook_event_name"] == "UserPromptSubmit"


def test_parse_hook_payload_treats_plain_text_as_prompt() -> None:
    payload = parse_hook_payload("테스트 실행해줘")

    assert extract_prompt(payload) == "테스트 실행해줘"


def test_extract_prompt_searches_nested_payload() -> None:
    payload = {"payload": {"message": {"text": "nested prompt"}}}

    assert extract_prompt(payload) == "nested prompt"


def test_extract_metadata_defaults_to_codex_source() -> None:
    assert extract_metadata({})["source"] == "codex-user-prompt-submit"


def test_extract_metadata_accepts_custom_source() -> None:
    payload = {"hook_event_name": "UserPromptSubmit"}

    metadata = extract_metadata(payload, source="claude-user-prompt-submit")

    assert metadata["source"] == "claude-user-prompt-submit"
    assert metadata["hook_event_name"] == "UserPromptSubmit"

from harnex_memory.core.prompt_store import (
    append_prompt_record,
    normalize_prompt,
    read_prompt_records,
)


def test_append_and_read_prompt_records(tmp_path):
    append_prompt_record(
        tmp_path,
        prompt="  같은   프롬프트  ",
        source="unit-test",
        metadata={"phase": "clarify"},
    )

    records = read_prompt_records(tmp_path)

    assert len(records) == 1
    assert records[0].prompt == "  같은   프롬프트  "
    assert records[0].metadata == {"phase": "clarify"}


def test_normalize_prompt_collapses_case_and_spacing():
    assert normalize_prompt(" Run   PYTEST ") == "run pytest"

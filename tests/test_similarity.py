import pytest

from harnex_memory.core.analyzer import suggest_candidates
from harnex_memory.core.models import PromptRecord
from harnex_memory.core.similarity import EmbeddingMatcher, LexicalMatcher, resolve_matcher

# Deterministic stand-in for a local embedding model: paraphrases map to nearly
# identical vectors, unrelated prompts to orthogonal ones. Keeps the clustering
# logic testable without downloading a real model.
_VECTORS = {
    "테스트 실행해줘": [1.0, 0.0, 0.0],
    "test 돌려줘": [0.98, 0.02, 0.0],
    "배포해줘": [0.0, 1.0, 0.0],
}


def _fake_embed(texts: list[str]) -> list[list[float]]:
    return [_VECTORS[text] for text in texts]


def test_lexical_matcher_groups_identical_after_normalization():
    clusters = LexicalMatcher().cluster(["pytest 실행", " pytest   실행 ", "배포"])

    assert sorted(len(cluster) for cluster in clusters) == [1, 2]


def test_embedding_matcher_clusters_semantically_similar():
    matcher = EmbeddingMatcher(_fake_embed, threshold=0.9)

    clusters = matcher.cluster(["테스트 실행해줘", "test 돌려줘", "배포해줘"])

    assert sorted(sorted(cluster) for cluster in clusters) == [[0, 1], [2]]


def test_suggest_candidates_finds_paraphrase_only_with_semantic_matcher(tmp_path):
    records = [
        PromptRecord(prompt="테스트 실행해줘", source="adapter", project_root=str(tmp_path)),
        PromptRecord(prompt="test 돌려줘", source="adapter", project_root=str(tmp_path)),
    ]

    # Lexically the two prompts differ → the default lexical matcher finds nothing.
    assert suggest_candidates(records, project_root=tmp_path) == []

    # Semantically they are the same request → a single repeated-prompt candidate.
    candidates = suggest_candidates(
        records,
        project_root=tmp_path,
        matcher=EmbeddingMatcher(_fake_embed, threshold=0.9),
    )
    assert len(candidates) == 1
    assert len(candidates[0].evidence) == 2


def test_resolve_matcher_defaults_to_lexical(monkeypatch):
    monkeypatch.delenv("HARNEX_MEMORY_SIMILARITY", raising=False)

    assert isinstance(resolve_matcher(), LexicalMatcher)


def test_resolve_matcher_rejects_unknown_mode(monkeypatch):
    monkeypatch.setenv("HARNEX_MEMORY_SIMILARITY", "magic")

    with pytest.raises(ValueError):
        resolve_matcher()

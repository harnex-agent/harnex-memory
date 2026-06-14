"""Pluggable prompt-similarity matchers for repeated-prompt detection.

Detecting that two prompts are "the same request" is the heart of the repeated-
prompt suggestion. The default :class:`LexicalMatcher` groups prompts that are
identical after normalization (zero dependencies, fully deterministic) — but it
cannot see that "테스트 실행해줘" and "test 돌려줘" mean the same thing.

:class:`EmbeddingMatcher` closes that gap with **local** sentence embeddings and
cosine clustering — semantic matching with NO external API call. The embedding
backend is an optional dependency (``harnex-memory[embeddings]``); the clustering
logic itself takes an injected ``embed`` callable, so it is unit-testable without
downloading any model.

Selection is env-driven (see :func:`resolve_matcher`): unset/``lexical`` keeps the
dependency-free default; ``embedding`` activates local embeddings.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from math import sqrt
from typing import Protocol, runtime_checkable

from harnex_memory.core.prompt_store import normalize_prompt

SIMILARITY_ENV_VAR = "HARNEX_MEMORY_SIMILARITY"
EMBED_MODEL_ENV_VAR = "HARNEX_MEMORY_EMBED_MODEL"
EMBED_THRESHOLD_ENV_VAR = "HARNEX_MEMORY_EMBED_THRESHOLD"

# mpnet-base separates short multilingual commands cleanly (empirically: test-
# paraphrases cluster at ~0.8-0.9, cross-intent pairs sit at ~0.5); the lighter
# MiniLM variant cramps everything into ~0.97+ and cannot be thresholded. Both
# the model and threshold are overridable via env for other workloads.
DEFAULT_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
DEFAULT_EMBED_THRESHOLD = 0.62

Embedder = Callable[[list[str]], list[list[float]]]


@runtime_checkable
class SimilarityMatcher(Protocol):
    """Groups texts into clusters of same-meaning items."""

    def cluster(self, texts: list[str]) -> list[list[int]]:
        """Return clusters as lists of indices into ``texts``."""


class LexicalMatcher:
    """Cluster texts that are identical after normalization (the default)."""

    def cluster(self, texts: list[str]) -> list[list[int]]:
        groups: dict[str, list[int]] = {}
        for index, text in enumerate(texts):
            groups.setdefault(normalize_prompt(text), []).append(index)
        return list(groups.values())


class EmbeddingMatcher:
    """Cluster texts by cosine similarity of local embeddings.

    ``embed`` maps a list of texts to a list of vectors; injecting it keeps the
    clustering logic testable without a real model. Greedy single-representative
    clustering: each text joins the most similar existing cluster whose
    representative is within ``threshold``, otherwise it starts a new cluster.
    """

    def __init__(self, embed: Embedder, threshold: float = DEFAULT_EMBED_THRESHOLD) -> None:
        self._embed = embed
        self._threshold = threshold

    def cluster(self, texts: list[str]) -> list[list[int]]:
        if not texts:
            return []
        vectors = self._embed(list(texts))
        clusters: list[list[int]] = []
        representatives: list[list[float]] = []
        for index, vector in enumerate(vectors):
            best_cluster = -1
            best_similarity = self._threshold
            for cluster_index, representative in enumerate(representatives):
                similarity = _cosine(vector, representative)
                if similarity >= best_similarity:
                    best_similarity = similarity
                    best_cluster = cluster_index
            if best_cluster >= 0:
                clusters[best_cluster].append(index)
            else:
                clusters.append([index])
                representatives.append(vector)
        return clusters


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(x * y for x, y in zip(left, right))
    left_norm = sqrt(sum(x * x for x in left))
    right_norm = sqrt(sum(y * y for y in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def fastembed_embedder(model_name: str = DEFAULT_EMBED_MODEL) -> Embedder:
    """Build a local-embedding callable backed by fastembed (lazy import)."""
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:  # pragma: no cover - requires optional extra
        raise ImportError(
            "Semantic similarity needs the optional 'embeddings' extra: "
            "pip install 'harnex-memory[embeddings]'"
        ) from exc

    model = TextEmbedding(model_name=model_name)

    def embed(texts: list[str]) -> list[list[float]]:
        return [[float(value) for value in vector] for vector in model.embed(list(texts))]

    return embed


_EMBEDDING_CACHE: dict[tuple[str, float], SimilarityMatcher] = {}


def resolve_matcher() -> SimilarityMatcher:
    """Resolve the active matcher from the environment.

    Unset or ``lexical`` → :class:`LexicalMatcher` (default, no dependency).
    ``embedding`` → a cached :class:`EmbeddingMatcher` over local embeddings.
    """
    mode = os.environ.get(SIMILARITY_ENV_VAR, "lexical").strip().lower()
    if mode in ("", "lexical"):
        return LexicalMatcher()
    if mode == "embedding":
        model_name = os.environ.get(EMBED_MODEL_ENV_VAR, DEFAULT_EMBED_MODEL).strip()
        threshold = float(os.environ.get(EMBED_THRESHOLD_ENV_VAR, str(DEFAULT_EMBED_THRESHOLD)))
        key = (model_name, threshold)
        if key not in _EMBEDDING_CACHE:
            _EMBEDDING_CACHE[key] = EmbeddingMatcher(fastembed_embedder(model_name), threshold)
        return _EMBEDDING_CACHE[key]
    raise ValueError(f"Unknown {SIMILARITY_ENV_VAR}={mode!r} (use 'lexical' or 'embedding')")

from __future__ import annotations

import uuid

import pytest

from davos.modules.assistant.application.services.answer_fingerprint import AnswerFingerprint
from davos.modules.assistant.domain.services.cache_hit_selector import CacheHitSelector
from davos.modules.assistant.domain.value_objects.cache_candidate import CacheCandidate
from davos.modules.assistant.domain.value_objects.semantic_cache_policy import SemanticCachePolicy

selector = CacheHitSelector()


def candidate(similarity: float, signature: str = "", response: str = "پاسخ") -> CacheCandidate:
    return CacheCandidate(uuid.uuid4(), "پرسش", signature, response, (), similarity)


def test_the_most_similar_qualifying_entry_wins() -> None:
    best = candidate(0.95, response="بهترین")
    hit = selector.select([candidate(0.90), best, candidate(0.92)], signature="", threshold=0.88)
    assert hit is best


def test_an_entry_below_the_threshold_never_qualifies() -> None:
    assert selector.select([candidate(0.879)], signature="", threshold=0.88) is None


def test_an_entry_exactly_at_the_threshold_qualifies() -> None:
    assert selector.select([candidate(0.88)], signature="", threshold=0.88) is not None


def test_a_different_signature_disqualifies_even_a_near_identical_entry() -> None:
    assert selector.select([candidate(0.999, signature="n:140|w:")], signature="n:135|w:", threshold=0.88) is None


def test_a_lower_scoring_entry_with_the_right_signature_beats_a_higher_scoring_one_with_the_wrong_one() -> None:
    right = candidate(0.90, signature="n:|w:جمعه")
    hit = selector.select([candidate(0.99, signature="n:|w:شنبه"), right], signature="n:|w:جمعه", threshold=0.88)
    assert hit is right


def test_nothing_found_means_no_hit() -> None:
    assert selector.select([], signature="", threshold=0.88) is None


@pytest.mark.parametrize("threshold", [0.49, 1.01, -1.0])
def test_the_policy_rejects_a_threshold_outside_a_sensible_range(threshold: float) -> None:
    with pytest.raises(ValueError, match="similarity_threshold"):
        SemanticCachePolicy(similarity_threshold=threshold)


@pytest.mark.parametrize("field", ["candidate_limit", "max_age_days", "context_turns"])
def test_the_policy_rejects_non_positive_sizes(field: str) -> None:
    with pytest.raises(ValueError, match="positive"):
        SemanticCachePolicy(**{field: 0})


def test_the_default_policy_is_the_measured_one_not_the_one_from_the_brief() -> None:
    policy = SemanticCachePolicy()
    assert policy.similarity_threshold == 0.94  # measured on the real model, see docs/SEMANTIC_CACHE.md
    assert {t.value for t in policy.excluded_source_types} == {"policy"}


def test_the_fingerprint_changes_with_every_input_and_only_then() -> None:
    base = AnswerFingerprint(rules_version="r1", model="m1")
    reference = base.compute(knowledge_digest="k1", persona="p1")
    assert base.compute(knowledge_digest="k1", persona="p1") == reference
    assert base.compute(knowledge_digest="k2", persona="p1") != reference
    assert base.compute(knowledge_digest="k1", persona="p2") != reference
    assert AnswerFingerprint(rules_version="r2", model="m1").compute(knowledge_digest="k1", persona="p1") != reference
    assert AnswerFingerprint(rules_version="r1", model="m2").compute(knowledge_digest="k1", persona="p1") != reference


def test_moving_text_between_the_digest_and_the_persona_changes_the_fingerprint() -> None:
    fingerprint = AnswerFingerprint(rules_version="r", model="m")
    assert fingerprint.compute(knowledge_digest="ab", persona="c") != fingerprint.compute(
        knowledge_digest="a", persona="bc"
    )

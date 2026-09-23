"""The knowledge digest (real PostgreSQL) and the conversation memory (real Redis)."""

from __future__ import annotations

import json
import uuid

import pytest
from redis.asyncio import Redis

from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.adapters.context.redis_conversation_context import RedisConversationContext
from davos.modules.assistant.adapters.persistence.pg_knowledge_digest import PgKnowledgeDigest
from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn
from tests.support.assistant_knowledge import publish

pytestmark = pytest.mark.integration


# ---- knowledge digest --------------------------------------------------------------------------------------


async def test_the_digest_of_an_empty_knowledge_base_is_empty(cached_container: ApplicationContainer) -> None:
    digest = PgKnowledgeDigest(cached_container.session_factory, ttl_seconds=0)
    assert await digest.current() == ""


async def test_the_digest_changes_when_an_entry_is_added_edited_or_removed(
    cached_container: ApplicationContainer,
) -> None:
    digest = PgKnowledgeDigest(cached_container.session_factory, ttl_seconds=0)
    await publish(cached_container, "hours", "ساعت کاری", "شنبه تا چهارشنبه ۱۵ تا ۲۴", "/contact")
    first = await digest.current()
    assert len(first) == 32 and await digest.current() == first, "stable while nothing changes"

    await publish(cached_container, "hours", "ساعت کاری", "شنبه تا چهارشنبه ۱۵ تا ۲۳", "/contact")  # edited
    edited = await digest.current()
    assert edited != first

    await publish(cached_container, "price", "قیمت", "۷۹۰ هزار تومان", "/faq")  # added
    added = await digest.current()
    assert added not in {first, edited}


async def test_the_digest_is_remembered_for_its_lifetime_and_only_then_recomputed(
    cached_container: ApplicationContainer,
) -> None:
    digest = PgKnowledgeDigest(cached_container.session_factory, ttl_seconds=3600)
    await publish(cached_container, "hours", "ساعت کاری", "متن اول", "/contact")
    remembered = await digest.current()
    await publish(cached_container, "hours", "ساعت کاری", "متن دوم", "/contact")
    assert await digest.current() == remembered, "one query per lifetime, not one per question"
    fresh = PgKnowledgeDigest(cached_container.session_factory, ttl_seconds=3600)
    assert await fresh.current() != remembered


# ---- conversation memory -----------------------------------------------------------------------------------


def turn(n: int) -> ConversationTurn:
    return ConversationTurn(question=f"پرسش {n}", answer=f"پاسخ {n}")


async def test_the_redis_memory_keeps_the_latest_turns_oldest_first(redis_client: Redis) -> None:
    memory = RedisConversationContext(redis_client, max_turns=3, ttl_seconds=600)
    conversation = uuid.uuid4()
    for n in range(1, 6):
        await memory.append(conversation, turn(n))
    assert await memory.recent(conversation) == (turn(3), turn(4), turn(5))


async def test_the_redis_memory_expires_and_can_be_cleared(redis_client: Redis) -> None:
    memory = RedisConversationContext(redis_client, max_turns=3, ttl_seconds=600)
    kept, cleared = uuid.uuid4(), uuid.uuid4()
    await memory.append(kept, turn(1))
    await memory.append(cleared, turn(2))
    assert 0 < await redis_client.ttl(f"assistant:context:{kept}") <= 600

    await memory.clear(cleared)

    assert await memory.recent(cleared) == () and await memory.recent(kept) == (turn(1),)


async def test_persian_text_survives_redis_unescaped_and_a_damaged_item_is_skipped(redis_client: Redis) -> None:
    memory = RedisConversationContext(redis_client, max_turns=5, ttl_seconds=600)
    conversation = uuid.uuid4()
    await memory.append(conversation, ConversationTurn(question="هزینه‌ش چقدره؟", answer="۷۹۰ هزار تومان"))
    await redis_client.rpush(f"assistant:context:{conversation}", "not json", json.dumps({"q": "only a question"}))
    assert await memory.recent(conversation) == (ConversationTurn(question="هزینه‌ش چقدره؟", answer="۷۹۰ هزار تومان"),)
    raw = await redis_client.lindex(f"assistant:context:{conversation}", 0)
    assert "هزینه‌ش" in raw, "stored as readable text, not \\u escapes"

"""End to end: HTTP -> real container -> real PostgreSQL/pgvector cache; only the embedder and model are fakes."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.api.app_factory import create_app
from davos.composition.application_container import ApplicationContainer
from davos.platform.settings.app_settings import AppSettings
from tests.fakes.scripted_ai_chat import ScriptedAiChat
from tests.integration.api.conftest import CLIENT_IP
from tests.support.assistant_knowledge import publish

pytestmark = pytest.mark.integration

ASK = "/api/v1/assistant/ask"
HOURS = "ساعت کاری ما از ۱۵ تا ۲۴ است [1]."


@pytest.fixture
async def cached_api(
    cached_container: ApplicationContainer, test_settings: AppSettings
) -> AsyncIterator[httpx.AsyncClient]:
    await publish(cached_container, "hours", "زمان سانس‌ها (نمونه)", "شنبه تا چهارشنبه ۱۵ تا ۲۴", "/contact", kind="faq")
    app = create_app(test_settings, cached_container)
    transport = httpx.ASGITransport(app=app, client=(CLIENT_IP, 50000), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    await cached_container.drain_background_work()


async def ask(client: httpx.AsyncClient, container: ApplicationContainer, question: str, **extra: object) -> dict:
    response = await client.post(ASK, json={"question": question, **extra})
    assert response.status_code == 200, response.text
    await container.drain_background_work()  # the cache write happens after the response has gone out
    return response.json()


async def rows(engine: AsyncEngine, sql: str) -> list[dict]:
    async with engine.connect() as conn:
        return [dict(r) for r in (await conn.execute(text(sql))).mappings()]


async def test_the_second_identical_question_is_answered_from_pgvector_without_the_model(
    cached_api: httpx.AsyncClient,
    cached_container: ApplicationContainer,
    ai_chat: ScriptedAiChat,
    engine: AsyncEngine,
) -> None:
    ai_chat.reply = HOURS

    first = await ask(cached_api, cached_container, "ساعت کاری شما چیه؟")
    second = await ask(cached_api, cached_container, "ساعت کاری شما چیه؟")

    assert (first["outcome"], first["from_cache"]) == ("answered", False)
    assert (second["outcome"], second["from_cache"]) == ("answered", True)
    assert second["answer"] == first["answer"] == "ساعت کاری ما از ۱۵ تا ۲۴ است."
    assert second["sources"] == first["sources"] == [{"title": "زمان سانس‌ها (نمونه)", "url": "/contact"}]
    assert ai_chat.calls == 1

    (entry,) = await rows(
        engine,
        "SELECT hit_count, is_active, is_flagged_for_review, language, embedding_model, length(fingerprint) AS fp, "
        "original_query, resolved_query, vector_dims(embedding) AS dims FROM assistant_semantic_cache",
    )
    assert entry["hit_count"] == 1 and entry["is_active"] is True and entry["is_flagged_for_review"] is False
    assert (entry["language"], entry["embedding_model"], entry["fp"], entry["dims"]) == ("fa", "hashing-test", 64, 768)
    assert entry["original_query"] == "ساعت کاری شما چیه؟" and entry["resolved_query"] == "ساعت کاری شما چیه"

    interactions = await rows(
        engine,
        "SELECT served_from_cache, cache_entry_id, prompt_tokens FROM assistant_interactions ORDER BY occurred_at",
    )
    assert [i["served_from_cache"] for i in interactions] == [False, True]
    assert interactions[0]["cache_entry_id"] == interactions[1]["cache_entry_id"] is not None
    assert interactions[1]["prompt_tokens"] == 0


async def test_editing_a_knowledge_entry_stops_the_old_answer_being_served(
    cached_api: httpx.AsyncClient, cached_container: ApplicationContainer, ai_chat: ScriptedAiChat
) -> None:
    ai_chat.reply = HOURS
    await ask(cached_api, cached_container, "ساعت کاری شما چیه؟")
    await publish(cached_container, "hours", "زمان سانس‌ها (نمونه)", "شنبه تا چهارشنبه ۱۵ تا ۲۳", "/contact", kind="faq")

    again = await ask(cached_api, cached_container, "ساعت کاری شما چیه؟")

    assert again["from_cache"] is False and ai_chat.calls == 2


async def test_a_not_helpful_rating_retires_the_cached_answer(
    cached_api: httpx.AsyncClient,
    cached_container: ApplicationContainer,
    ai_chat: ScriptedAiChat,
    engine: AsyncEngine,
) -> None:
    ai_chat.reply = HOURS
    await ask(cached_api, cached_container, "ساعت کاری شما چیه؟")
    served = await ask(cached_api, cached_container, "ساعت کاری شما چیه؟")
    assert served["from_cache"] is True

    rated = await cached_api.post(
        f"/api/v1/assistant/answers/{served['interaction_id']}/feedback", json={"helpful": False}
    )
    assert rated.status_code == 204

    (entry,) = await rows(engine, "SELECT is_active, is_flagged_for_review FROM assistant_semantic_cache")
    assert entry == {"is_active": False, "is_flagged_for_review": True}
    third = await ask(cached_api, cached_container, "ساعت کاری شما چیه؟")
    assert third["from_cache"] is False and ai_chat.calls == 2


async def test_answers_that_cite_a_policy_are_not_cached(
    cached_api: httpx.AsyncClient,
    cached_container: ApplicationContainer,
    ai_chat: ScriptedAiChat,
    engine: AsyncEngine,
) -> None:
    await publish(cached_container, "ages", "شرایط سنی", "کودک زیر ۱۱ سال رانندگی نمی‌کند", "/faq", kind="policy")
    ai_chat.reply = "نه، زیر ۱۱ سال نمی‌تواند [1][2]."  # cites the FAQ entry and the policy

    await ask(cached_api, cached_container, "کودک ۱۰ ساله می‌تواند رانندگی کند؟")
    again = await ask(cached_api, cached_container, "کودک ۱۰ ساله می‌تواند رانندگی کند؟")

    assert again["from_cache"] is False and ai_chat.calls == 2
    assert await rows(engine, "SELECT id FROM assistant_semantic_cache") == []


async def test_a_conversation_follow_up_is_resolved_and_the_model_sees_the_history(
    cached_api: httpx.AsyncClient, cached_container: ApplicationContainer, ai_chat: ScriptedAiChat
) -> None:
    ai_chat.reply = HOURS
    conversation = "6f7cfa03-80e8-4bf4-ac14-ad09638f0154"
    await ask(cached_api, cached_container, "ساعت کاری شما چیه؟", conversation_id=conversation)
    await ask(cached_api, cached_container, "پنجشنبه چطور؟", conversation_id=conversation)
    assert "<history>" in ai_chat.user_prompt and "ساعت کاری شما چیه" in ai_chat.user_prompt


async def test_forget_it_clears_the_conversation_and_never_calls_the_model(
    cached_api: httpx.AsyncClient, cached_container: ApplicationContainer, ai_chat: ScriptedAiChat
) -> None:
    ai_chat.reply = HOURS
    conversation = "8a3ffbe9-b05d-406f-93a2-b30c2c29038d"
    await ask(cached_api, cached_container, "ساعت کاری شما چیه؟", conversation_id=conversation)
    calls = ai_chat.calls

    reset = await ask(cached_api, cached_container, "فراموشش کن", conversation_id=conversation)

    assert reset["outcome"] == "small_talk" and reset["sources"] == [] and ai_chat.calls == calls
    await ask(cached_api, cached_container, "پنجشنبه چطور؟", conversation_id=conversation)
    assert "<history>" not in ai_chat.user_prompt


async def test_the_response_says_where_an_answer_came_from_even_without_a_cache(
    api: httpx.AsyncClient, ai_chat: ScriptedAiChat
) -> None:
    response = await api.post(ASK, json={"question": "سلام"})
    assert response.json()["from_cache"] is False

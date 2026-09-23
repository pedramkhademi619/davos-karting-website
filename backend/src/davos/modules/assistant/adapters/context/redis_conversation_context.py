from __future__ import annotations

import json
import uuid

from redis.asyncio import Redis

from davos.modules.assistant.application.ports.conversation_context_port import ConversationContextPort
from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn


class RedisConversationContext(ConversationContextPort):
    """The last few exchanges of a conversation, shared by every API replica and forgotten after ``ttl_seconds``.

    Nothing is written to the database: this is working memory for understanding a follow-up, kept only for as long as
    the conversation is plausibly still going on.
    """

    def __init__(self, redis: Redis, *, max_turns: int, ttl_seconds: int) -> None:
        self._redis = redis
        self._max_turns = max_turns
        self._ttl = ttl_seconds

    @staticmethod
    def _key(conversation_id: uuid.UUID) -> str:
        return f"assistant:context:{conversation_id}"

    async def recent(self, conversation_id: uuid.UUID) -> tuple[ConversationTurn, ...]:
        raw = await self._redis.lrange(self._key(conversation_id), 0, -1)
        turns: list[ConversationTurn] = []
        for item in raw:
            try:
                data = json.loads(item)
                turns.append(ConversationTurn(question=str(data["q"]), answer=str(data["a"])))
            except (ValueError, KeyError, TypeError):
                continue  # a damaged item is skipped rather than failing the question
        return tuple(turns)

    async def append(self, conversation_id: uuid.UUID, turn: ConversationTurn) -> None:
        key = self._key(conversation_id)
        payload = json.dumps({"q": turn.question, "a": turn.answer}, ensure_ascii=False)
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.rpush(key, payload)
            pipe.ltrim(key, -self._max_turns, -1)
            pipe.expire(key, self._ttl)
            await pipe.execute()

    async def clear(self, conversation_id: uuid.UUID) -> None:
        await self._redis.delete(self._key(conversation_id))

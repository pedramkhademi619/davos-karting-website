# ruff: noqa: F401, F811  (pytest fixtures are imported from the accounting flow tests and then used by name)
"""The panel's own helper: staff-only, apart from the customer assistant, and told the whole workflow."""

from __future__ import annotations

import httpx
import pytest

from tests.integration.accounting.test_accounting_flow import (
    ORIGIN,
    admin_api,
    container,
    login,
)

pytestmark = pytest.mark.integration


async def test_only_signed_in_staff_can_ask_and_the_guide_text_is_what_the_model_is_told(
    admin_api: httpx.AsyncClient,
    container,
) -> None:
    body = {"messages": [{"role": "user", "content": "فروش حضوری را چطور ثبت کنم؟"}]}
    assert (await admin_api.post("/api/v1/admin/guide/ask", json=body, headers={"Origin": ORIGIN})).status_code == 401
    headers = await login(admin_api)
    answer = await admin_api.post("/api/v1/admin/guide/ask", json=body, headers=headers)
    assert answer.status_code == 200 and answer.json()["answer"] == "x"  # ScriptedAiChat's fixed reply
    system = container.ai_chat.requests[-1].messages[0]
    assert "ثبت فروش حضوری" in system.content and "شماره بلیت" in system.content
    assert container.ai_chat.requests[-1].messages[-1].content == "فروش حضوری را چطور ثبت کنم؟"
    empty = await admin_api.post("/api/v1/admin/guide/ask", json={"messages": []}, headers=headers)
    assert empty.status_code == 422


async def test_the_guide_never_ends_on_the_assistants_own_turn(admin_api: httpx.AsyncClient) -> None:
    headers = await login(admin_api)
    body = {"messages": [{"role": "user", "content": "سلام"}, {"role": "assistant", "content": "سلام!"}]}
    answer = await admin_api.post("/api/v1/admin/guide/ask", json=body, headers=headers)
    assert answer.status_code == 200 and "سؤالتان" in answer.json()["answer"]

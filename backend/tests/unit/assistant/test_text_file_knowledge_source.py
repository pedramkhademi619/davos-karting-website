from __future__ import annotations

from pathlib import Path

import pytest

from davos.modules.assistant.adapters.knowledge.text_file_knowledge_source import (
    MAX_FILE_BYTES,
    TextFileKnowledgeSource,
)
from davos.modules.assistant.application.ports.knowledge_source_unavailable_error import KnowledgeSourceUnavailableError
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType

FULL = """# note for the editor
title: چطور نوبت رزرو کنم؟
url: /faq
type: service
status: published

رزرو از دکمه بالای سایت انجام می‌شود.

خط دوم با فاصله.
"""


def _folder(tmp_path: Path, **files: str) -> Path:
    for name, text in files.items():
        (tmp_path / f"{name}.txt").write_text(text, encoding="utf-8")
    return tmp_path


def _only_problem(tmp_path: Path, text: str) -> str:
    batch = TextFileKnowledgeSource(_folder(tmp_path, doc=text)).read_all()
    assert batch.documents == ()
    assert [p.name for p in batch.problems] == ["doc"]
    return batch.problems[0].reason


def test_parses_a_full_document(tmp_path: Path) -> None:
    (document,) = TextFileKnowledgeSource(_folder(tmp_path, booking=FULL)).read_all().documents
    assert document.ref == "booking"
    assert document.title == "چطور نوبت رزرو کنم؟"
    assert document.url == "/faq"
    assert document.source_type is KnowledgeSourceType.SERVICE
    assert document.published is True
    assert document.body == "رزرو از دکمه بالای سایت انجام می‌شود.\n\nخط دوم با فاصله."


def test_type_and_status_are_optional_and_default_to_a_published_faq(tmp_path: Path) -> None:
    (document,) = TextFileKnowledgeSource(_folder(tmp_path, a="title: عنوان\nurl: /x\n\nمتن")).read_all().documents
    assert document.source_type is KnowledgeSourceType.FAQ and document.published is True


def test_draft_documents_are_read_but_marked_unpublished(tmp_path: Path) -> None:
    text = "title: عنوان\nurl: /x\nstatus: draft\n\nمتن"
    (document,) = TextFileKnowledgeSource(_folder(tmp_path, a=text)).read_all().documents
    assert document.published is False


def test_keys_and_values_are_forgiving_about_case_and_spaces(tmp_path: Path) -> None:
    text = "  Title :   عنوان  \nURL: /x\nType: POLICY\nStatus: Draft\n\nمتن"
    (document,) = TextFileKnowledgeSource(_folder(tmp_path, a=text)).read_all().documents
    assert (document.title, document.url, document.source_type, document.published) == (
        "عنوان",
        "/x",
        KnowledgeSourceType.POLICY,
        False,
    )


def test_leading_blank_lines_and_a_byte_order_mark_are_tolerated(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes("﻿\n\n# c\ntitle: عنوان\nurl: /x\n\nمتن".encode())
    assert TextFileKnowledgeSource(tmp_path).read_all().documents[0].title == "عنوان"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("url: /x\n\nمتن", "title"),
        ("title: عنوان\n\nمتن", "url"),
        ("title: عنوان\nurl: /x\n\n", "خالی"),
        ("title: عنوان\nurl: /x", "خالی"),
        ("title: عنوان\nurl: /x\nمتن بدون خط خالی", "خط خالی"),
        ("title: عنوان\nurl: /x\nautor: من\n\nمتن", "autor"),
        ("title: عنوان\nurl: /x\ntype: blog\n\nمتن", "faq"),
        ("title: عنوان\nurl: /x\nstatus: maybe\n\nمتن", "published"),
    ],
)
def test_each_mistake_is_reported_with_a_reason_the_editor_can_act_on(tmp_path: Path, text: str, expected: str) -> None:
    assert expected in _only_problem(tmp_path, text)


def test_one_broken_file_does_not_hide_the_good_ones(tmp_path: Path) -> None:
    _folder(tmp_path, good="title: عنوان\nurl: /x\n\nمتن", bad="title only")
    batch = TextFileKnowledgeSource(tmp_path).read_all()
    assert [d.ref for d in batch.documents] == ["good"]
    assert [p.name for p in batch.problems] == ["bad"]


def test_files_that_are_too_big_or_not_utf8_are_problems(tmp_path: Path) -> None:
    (tmp_path / "big.txt").write_text("x" * (MAX_FILE_BYTES + 1), encoding="utf-8")
    (tmp_path / "latin.txt").write_bytes(b"title: \xe9\xe8\nurl: /x\n\nbody \xff")
    reasons = {p.name: p.reason for p in TextFileKnowledgeSource(tmp_path).read_all().problems}
    assert "۶۴" in reasons["big"] and "UTF-8" in reasons["latin"]


def test_only_txt_files_are_read_and_in_a_stable_order(tmp_path: Path) -> None:
    for name in ("b", "a", "c"):
        (tmp_path / f"{name}.txt").write_text(f"title: {name}\nurl: /{name}\n\nمتن", encoding="utf-8")
    (tmp_path / "notes.md").write_text("title: no\nurl: /no\n\nno", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    assert [d.ref for d in TextFileKnowledgeSource(tmp_path).read_all().documents] == ["a", "b", "c"]


def test_a_missing_folder_is_an_error_not_an_empty_knowledge_base(tmp_path: Path) -> None:
    with pytest.raises(KnowledgeSourceUnavailableError):
        TextFileKnowledgeSource(tmp_path / "not-mounted").read_all()

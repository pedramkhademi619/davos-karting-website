from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

from davos.modules.assistant.adapters.persona.file_assistant_persona import MAX_PERSONA_CHARS, FileAssistantPersona
from davos.modules.assistant.application.messages import assistant_messages as messages

SECRET_NOTE = "لحن دوستانه داشته باش."


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_no_path_means_the_built_in_notes() -> None:
    assert FileAssistantPersona("").text() == messages.DEFAULT_PERSONA


def test_reads_the_file_and_drops_comment_lines(tmp_path: Path) -> None:
    file = _write(
        tmp_path / "persona.txt", f"# note for the editor\n{SECRET_NOTE}\n  # indented comment\nکوتاه بنویس.\n"
    )
    assert FileAssistantPersona(str(file)).text() == f"{SECRET_NOTE}\nکوتاه بنویس."


def test_an_empty_file_means_no_extra_notes_rather_than_the_default(tmp_path: Path) -> None:
    file = _write(tmp_path / "persona.txt", "# only comments\n\n")
    assert FileAssistantPersona(str(file)).text() == ""


def test_a_missing_file_falls_back_to_the_defaults_and_warns_only_once(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    persona = FileAssistantPersona(str(tmp_path / "nope.txt"))
    with caplog.at_level(logging.WARNING):
        assert persona.text() == messages.DEFAULT_PERSONA
        assert persona.text() == messages.DEFAULT_PERSONA
    assert len([r for r in caplog.records if "persona file" in r.getMessage()]) == 1


def test_edits_apply_without_a_restart(tmp_path: Path) -> None:
    file = _write(tmp_path / "persona.txt", "نسخه اول")
    persona = FileAssistantPersona(str(file))
    assert persona.text() == "نسخه اول"
    _write(file, "نسخه دوم و بلندتر")
    assert persona.text() == "نسخه دوم و بلندتر"


def test_the_file_is_only_read_again_when_it_changes(tmp_path: Path) -> None:
    file = _write(tmp_path / "persona.txt", "متن")
    persona = FileAssistantPersona(str(file))
    persona.text()
    stamp = persona._stamp
    persona.text()
    assert persona._stamp == stamp


def test_control_characters_are_removed(tmp_path: Path) -> None:
    file = _write(tmp_path / "persona.txt", "سلام\x00\x07 دنیا\x1b")
    assert FileAssistantPersona(str(file)).text() == "سلام دنیا"


def test_overlong_notes_are_cut_and_the_content_is_never_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    file = _write(tmp_path / "persona.txt", "الف" * (MAX_PERSONA_CHARS + 500))
    with caplog.at_level(logging.WARNING):
        text = FileAssistantPersona(str(file)).text()
    assert len(text) == MAX_PERSONA_CHARS
    assert "الف" * 10 not in caplog.text


def test_a_file_that_is_not_utf8_falls_back(tmp_path: Path) -> None:
    file = tmp_path / "persona.txt"
    file.write_bytes(b"\xff\xfe\xfa\xfb not utf8 \xc3\x28")
    assert FileAssistantPersona(str(file)).text() == messages.DEFAULT_PERSONA


def test_a_byte_order_mark_from_a_windows_editor_is_ignored(tmp_path: Path) -> None:
    file = tmp_path / "persona.txt"
    file.write_bytes("﻿سلام".encode())
    assert FileAssistantPersona(str(file)).text() == "سلام"


def test_edits_are_noticed_even_when_the_timestamp_does_not_change(tmp_path: Path) -> None:
    file = _write(tmp_path / "persona.txt", "aaaa")
    persona = FileAssistantPersona(str(file))
    assert persona.text() == "aaaa"
    before = file.stat()
    _write(file, "bbbbbbbb")
    os.utime(file, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert persona.text() == "bbbbbbbb"

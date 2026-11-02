"""Unit tests for message builder helpers."""

from __future__ import annotations

import pytest

from khulnasoft.ai.types.builders import (
    assistant_message,
    content_output,
    file_part,
    message,
    system_message,
    text_part,
    thinking,
    tool_message,
    tool_result_part,
    user_message,
)


class TestMessage:
    def test_with_text(self):
        msg = message("hello", role="user")
        assert msg.role == "user"
        assert len(msg.parts) == 1
        assert msg.parts[0].text == "hello"

    def test_with_part(self):
        msg = message(text_part("hello"), role="user")
        assert msg.role == "user"
        assert len(msg.parts) == 1
        assert msg.parts[0].text == "hello"

    def test_mixed_content(self):
        msg = message("hello", text_part(" world"), role="assistant")
        assert msg.role == "assistant"
        assert len(msg.parts) == 2
        assert msg.parts[0].text == "hello"
        assert msg.parts[1].text == " world"

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            message(42, role="user")  # type: ignore[arg-type]


class TestUserMessage:
    def test_creates_user_role(self):
        msg = user_message("hello")
        assert msg.role == "user"
        assert msg.parts[0].text == "hello"


class TestSystemMessage:
    def test_creates_system_role(self):
        msg = system_message("instructions")
        assert msg.role == "system"
        assert msg.parts[0].text == "instructions"


class TestAssistantMessage:
    def test_creates_assistant_role(self):
        msg = assistant_message("response")
        assert msg.role == "assistant"
        assert msg.parts[0].text == "response"


class TestToolMessage:
    def test_creates_tool_message_with_kwargs(self):
        msg = tool_message(tool_call_id="tc-1", result="ok")
        assert msg.role == "tool"
        assert len(msg.parts) == 1
        assert msg.parts[0].tool_call_id == "tc-1"


class TestTextPart:
    def test_creates_text_part(self):
        part = text_part("hello")
        assert part.text == "hello"


class TestFilePart:
    def test_creates_file_part(self):
        part = file_part(b"\x89PNG", media_type="image/png")
        assert part.media_type == "image/png"
        assert part.data == b"\x89PNG"


class TestContentOutput:
    def test_creates_content_output(self):
        co = content_output(text_part("a"), text_part("b"))
        assert len(co.value) == 2
        assert co.value[0].text == "a"
        assert co.value[1].text == "b"


class TestToolResultPart:
    def test_creates_tool_result_part(self):
        part = tool_result_part("tc-1", result="success")
        assert part.tool_call_id == "tc-1"
        assert part.result == "success"
        assert part.result_kind == "json"

    def test_creates_error_tool_result_part(self):
        part = tool_result_part("tc-1", result="failed", is_error=True)
        assert part.result_kind == "error"


class TestThinking:
    def test_creates_thinking(self):
        t = thinking("thoughts")
        assert t.text == "thoughts"

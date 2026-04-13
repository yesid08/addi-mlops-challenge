import os

import pytest
from pydantic import ValidationError

os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-key-for-tests")

from app.schemas import ChatRequest  # noqa: E402


def test_valid_request():
    req = ChatRequest(user_id="user_001", conversation_id="conv-1", message="Hola")
    assert req.user_id == "user_001"
    assert req.conversation_id == "conv-1"
    assert req.message == "Hola"


def test_all_valid_user_ids():
    for i in range(1, 9):
        uid = f"user_{i:03d}"
        req = ChatRequest(user_id=uid, conversation_id="c", message="test")
        assert req.user_id == uid


def test_invalid_user_id_raises():
    with pytest.raises(ValidationError, match="not found"):
        ChatRequest(user_id="user_999", conversation_id="c", message="Hola")


def test_unknown_string_user_id_raises():
    with pytest.raises(ValidationError):
        ChatRequest(user_id="admin", conversation_id="c", message="Hola")


def test_empty_message_raises():
    with pytest.raises(ValidationError):
        ChatRequest(user_id="user_001", conversation_id="c", message="")


def test_message_too_long_raises():
    with pytest.raises(ValidationError):
        ChatRequest(user_id="user_001", conversation_id="c", message="x" * 4001)


def test_message_at_max_length_ok():
    req = ChatRequest(user_id="user_001", conversation_id="c", message="x" * 4000)
    assert len(req.message) == 4000


def test_invalid_conversation_id_spaces():
    with pytest.raises(ValidationError, match="alphanumeric"):
        ChatRequest(user_id="user_001", conversation_id="conv 1", message="Hola")


def test_invalid_conversation_id_special_chars():
    with pytest.raises(ValidationError):
        ChatRequest(user_id="user_001", conversation_id="conv@1!", message="Hola")


def test_valid_conversation_id_with_hyphens_and_underscores():
    req = ChatRequest(
        user_id="user_001", conversation_id="conv_1-abc", message="Hola"
    )
    assert req.conversation_id == "conv_1-abc"

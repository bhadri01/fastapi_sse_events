"""Tests for configuration module."""

import pytest

from fastapi_sse_events.config import RealtimeConfig


def test_default_config():
    """Test default configuration values."""
    config = RealtimeConfig()

    assert config.redis_url == "redis://localhost:6379/0"
    assert config.heartbeat_seconds == 15
    assert config.sse_path == "/events"
    assert config.topic_prefix == ""


def test_custom_config():
    """Test custom configuration values."""
    config = RealtimeConfig(
        redis_url="redis://custom:6380/1",
        heartbeat_seconds=30,
        sse_path="/custom-events",
        topic_prefix="prod",
    )

    assert config.redis_url == "redis://custom:6380/1"
    assert config.heartbeat_seconds == 30
    assert config.sse_path == "/custom-events"
    assert config.topic_prefix == "prod"


def test_config_from_env(monkeypatch):
    """Test configuration from environment variables."""
    monkeypatch.setenv("SSE_REDIS_URL", "redis://env:6379/0")
    monkeypatch.setenv("SSE_HEARTBEAT_SECONDS", "20")
    monkeypatch.setenv("SSE_SSE_PATH", "/env-events")
    monkeypatch.setenv("SSE_TOPIC_PREFIX", "dev")

    config = RealtimeConfig()

    assert config.redis_url == "redis://env:6379/0"
    assert config.heartbeat_seconds == 20
    assert config.sse_path == "/env-events"
    assert config.topic_prefix == "dev"


def test_heartbeat_validation():
    """Test heartbeat seconds validation."""
    # Valid values
    config = RealtimeConfig(heartbeat_seconds=5)
    assert config.heartbeat_seconds == 5

    config = RealtimeConfig(heartbeat_seconds=60)
    assert config.heartbeat_seconds == 60

    # Invalid values
    with pytest.raises(ValueError):
        RealtimeConfig(heartbeat_seconds=4)  # Too small

    with pytest.raises(ValueError):
        RealtimeConfig(heartbeat_seconds=61)  # Too large


def test_get_topic_without_prefix():
    """Test topic name without prefix."""
    config = RealtimeConfig()
    topic = config.get_topic("comment_thread:123")

    assert topic == "comment_thread:123"


def test_get_topic_with_prefix():
    """Test topic name with prefix."""
    config = RealtimeConfig(topic_prefix="prod")
    topic = config.get_topic("comment_thread:123")

    assert topic == "prod:comment_thread:123"

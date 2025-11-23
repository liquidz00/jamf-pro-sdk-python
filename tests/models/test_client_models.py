"""Tests for client models."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest
from src.jamf_pro_sdk.models.client import AccessToken, Schemes, SessionConfig

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestSessionConfig:
    """Test SessionConfig model."""

    def test_session_config_defaults(self) -> None:
        """Test SessionConfig with default values."""
        config = SessionConfig()
        assert config.max_concurrency == 5
        assert config.return_exceptions is True
        assert config.verify is True
        assert config.scheme == Schemes.https

    def test_session_config_custom_values(self) -> None:
        """Test SessionConfig with custom values."""
        config = SessionConfig(
            timeout=30,
            max_concurrency=10,
            return_exceptions=False,
            verify=False,
            scheme=Schemes.http,
        )
        assert config.timeout == 30
        assert config.max_concurrency == 10
        assert config.return_exceptions is False
        assert config.verify is False
        assert config.scheme == Schemes.http


class TestAccessToken:
    """Test AccessToken model."""

    def test_access_token_initialization(self) -> None:
        """Test AccessToken initialization."""
        token = AccessToken()
        assert token.type == ""
        assert token.token == ""
        assert token.scope is None

    def test_access_token_with_values(self) -> None:
        """Test AccessToken with values."""
        expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
        token = AccessToken(
            type="user", token="test_token_123", expires=expires, scope=["read", "write"]
        )
        assert token.type == "user"
        assert token.token == "test_token_123"
        assert token.scope == ["read", "write"]

    def test_access_token_is_expired_false(self) -> None:
        """Test AccessToken is_expired property with valid token."""
        expires = datetime.now(timezone.utc) + timedelta(seconds=100)
        token = AccessToken(type="user", token="test", expires=expires)
        assert token.is_expired is False

    def test_access_token_is_expired_true(self) -> None:
        """Test AccessToken is_expired property with expired token."""
        expires = datetime.now(timezone.utc) - timedelta(seconds=100)
        token = AccessToken(type="user", token="test", expires=expires)
        assert token.is_expired is True

    def test_access_token_seconds_remaining(self) -> None:
        """Test AccessToken seconds_remaining property."""
        expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
        token = AccessToken(type="user", token="test", expires=expires)
        assert 3590 < token.seconds_remaining < 3610

    def test_access_token_seconds_remaining_expired(self) -> None:
        """Test AccessToken seconds_remaining with expired token."""
        expires = datetime.now(timezone.utc) - timedelta(seconds=100)
        token = AccessToken(type="user", token="test", expires=expires)
        assert token.seconds_remaining == 0

    def test_access_token_str(self) -> None:
        """Test AccessToken string representation."""
        token = AccessToken(token="test_token_123")
        assert str(token) == "test_token_123"

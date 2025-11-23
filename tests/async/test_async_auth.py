"""Tests for asynchronous authentication providers."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, Mock

import httpx
import pytest
from src.jamf_pro_sdk.clients.auth import (
    ApiClientCredentialsProvider,
    UserCredentialsProvider,
)
from src.jamf_pro_sdk.models.client import AccessToken

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_async_client(mocker: "MockerFixture") -> MagicMock:
    """Create a mock AsyncJamfProClient."""
    mock = MagicMock()
    mock.base_server_url = "https://test.jamfcloud.com"
    mock.async_client = AsyncMock()
    return mock


@pytest.mark.asyncio
class TestAsyncUserCredentialsProvider:
    """Test async UserCredentialsProvider."""

    async def test_get_access_token_async_success(
        self, mock_async_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """Test successful async access token acquisition."""
        provider = UserCredentialsProvider(username="test_user", password="test_pass")
        provider.attach_async_client(mock_async_client)

        expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        # resp.json() is called synchronously in the code, not awaited
        mock_response.json.return_value = {
            "token": "test_token_123",
            "expires": expires.isoformat(),
        }
        mock_response.raise_for_status = Mock()
        mock_async_client.async_client.post = AsyncMock(return_value=mock_response)

        token = await provider.get_access_token_async()
        assert token.token == "test_token_123"
        assert token.type == "user"

    async def test_refresh_access_token_async_new_token(
        self, mock_async_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """Test async token refresh when new token is needed."""
        provider = UserCredentialsProvider(username="test_user", password="test_pass")
        provider.attach_async_client(mock_async_client)

        expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        # resp.json() is called synchronously, not awaited
        mock_response.json.return_value = {"token": "new_token_123", "expires": expires.isoformat()}
        mock_response.raise_for_status = Mock()
        mock_async_client.async_client.post = AsyncMock(return_value=mock_response)

        await provider._refresh_access_token_async()
        assert provider._access_token.token == "new_token_123"

    async def test_keep_alive_async(
        self, mock_async_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """Test async keep-alive token refresh."""
        provider = UserCredentialsProvider(username="test_user", password="test_pass")
        provider.attach_async_client(mock_async_client)

        expires = datetime.now(timezone.utc) + timedelta(seconds=30)
        provider._access_token = AccessToken(type="user", token="existing_token", expires=expires)

        new_expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        # resp.json() is called synchronously, not awaited
        mock_response.json.return_value = {
            "token": "refreshed_token",
            "expires": new_expires.isoformat(),
        }
        mock_response.raise_for_status = Mock()
        mock_async_client.async_client.post = AsyncMock(return_value=mock_response)

        token = await provider._keep_alive_async()
        assert token.token == "refreshed_token"


@pytest.mark.asyncio
class TestAsyncApiClientCredentialsProvider:
    """Test async ApiClientCredentialsProvider."""

    async def test_request_access_token_async_success(
        self, mock_async_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """Test successful async OAuth token request."""
        provider = ApiClientCredentialsProvider(
            client_id="test_client_id", client_secret="test_secret"
        )
        provider.attach_async_client(mock_async_client)

        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        # resp.json() is called synchronously, not awaited
        mock_response.json.return_value = {
            "access_token": "oauth_token_123",
            "expires_in": 3600,
            "scope": "read write",
        }
        mock_response.raise_for_status = Mock()
        mock_async_client.async_client.post = AsyncMock(return_value=mock_response)

        token = await provider._request_access_token_async()
        assert token.token == "oauth_token_123"
        assert token.type == "oauth"
        assert token.scope == ["read", "write"]

    async def test_concurrent_async_token_requests(
        self, mock_async_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """Test concurrent async token requests."""
        provider = UserCredentialsProvider(username="test_user", password="test_pass")
        provider.attach_async_client(mock_async_client)

        expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        # resp.json() is called synchronously, not awaited
        mock_response.json.return_value = {"token": "test_token", "expires": expires.isoformat()}
        mock_response.raise_for_status = Mock()
        mock_async_client.async_client.post = AsyncMock(return_value=mock_response)

        import asyncio

        tasks = [provider.get_access_token_async() for _ in range(5)]
        tokens = await asyncio.gather(*tasks)

        assert len(tokens) == 5
        assert all(token.token == "test_token" for token in tokens)

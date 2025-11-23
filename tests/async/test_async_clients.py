"""Tests for AsyncJamfProClient asynchronous functionality."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest
from src.jamf_pro_sdk.clients import AsyncJamfProClient
from src.jamf_pro_sdk.clients.auth import UserCredentialsProvider
from src.jamf_pro_sdk.models.client import Schemes, SessionConfig

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_credentials() -> UserCredentialsProvider:
    """Create a mock credentials provider."""
    return UserCredentialsProvider(username="test_user", password="test_pass")


@pytest.fixture
def mock_async_client(mocker: "MockerFixture") -> MagicMock:
    """Create a mock httpx.AsyncClient."""
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json = AsyncMock(
        return_value={"token": "mock_token", "expires": "2024-01-01T00:00:00Z"}
    )
    mock_response.raise_for_status = Mock()
    mock_client.request = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.mark.asyncio
class TestAsyncJamfProClientInitialization:
    """Test AsyncJamfProClient initialization."""

    async def test_client_initialization_defaults(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """Test client initialization with default parameters."""
        with patch("src.jamf_pro_sdk.clients.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            client = AsyncJamfProClient(server="test.jamfcloud.com", credentials=mock_credentials)

            assert client.base_server_url == "https://test.jamfcloud.com:443"
            assert client.session_config.max_concurrency == 5
            assert client.classic_api is not None
            assert client.pro_api is not None

    async def test_client_initialization_custom_config(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """Test client initialization with custom session config."""
        with patch("src.jamf_pro_sdk.clients.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            session_config = SessionConfig(timeout=30, max_concurrency=10, return_exceptions=False)
            client = AsyncJamfProClient(
                server="test.jamfcloud.com",
                credentials=mock_credentials,
                session_config=session_config,
            )

            assert client.session_config.timeout == 30
            assert client.session_config.max_concurrency == 10


@pytest.mark.asyncio
class TestAsyncJamfProClientContextManager:
    """Test AsyncJamfProClient context manager."""

    async def test_async_context_manager_entry(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """Test async context manager entry."""
        with patch("src.jamf_pro_sdk.clients.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            from datetime import datetime, timedelta, timezone

            expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
            mock_response.json = AsyncMock(
                return_value={"token": "test", "expires": expires.isoformat()}
            )
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            async with AsyncJamfProClient(
                server="test.jamfcloud.com", credentials=mock_credentials
            ) as client:
                assert client is not None
                assert isinstance(client, AsyncJamfProClient)

    async def test_async_context_manager_exit(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """Test async context manager exit and cleanup."""
        with patch("src.jamf_pro_sdk.clients.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.aclose = AsyncMock()
            mock_client_class.return_value = mock_client_instance

            async with AsyncJamfProClient(
                server="test.jamfcloud.com", credentials=mock_credentials
            ) as client:
                pass

            mock_client_instance.aclose.assert_called_once()


@pytest.mark.asyncio
class TestAsyncJamfProClientConcurrentOperations:
    """Test AsyncJamfProClient concurrent operations."""

    async def test_async_concurrent_api_requests(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """Test async concurrent API requests."""
        with patch("src.jamf_pro_sdk.clients.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = {"token": "test", "expires": "2024-01-01T00:00:00Z"}
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            client = AsyncJamfProClient(server="test.jamfcloud.com", credentials=mock_credentials)

            async def mock_handler(arg: int) -> int:
                return arg

            results = []
            async for result in client.async_concurrent_api_requests(mock_handler, [1, 2, 3]):
                results.append(result)

            assert len(results) == 3
            assert results == [1, 2, 3]

    async def test_async_concurrent_api_requests_with_exceptions(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """Test async concurrent requests with exception handling."""
        with patch("src.jamf_pro_sdk.clients.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = {"token": "test", "expires": "2024-01-01T00:00:00Z"}
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            session_config = SessionConfig(return_exceptions=True)
            client = AsyncJamfProClient(
                server="test.jamfcloud.com",
                credentials=mock_credentials,
                session_config=session_config,
            )

            async def mock_handler(arg: int) -> int:
                if arg == 2:
                    raise ValueError("Test error")
                return arg

            results = []
            async for result in client.async_concurrent_api_requests(mock_handler, [1, 2, 3]):
                results.append(result)

            assert len(results) == 3
            # With return_exceptions=True, exceptions are returned
            assert any(isinstance(r, ValueError) for r in results)

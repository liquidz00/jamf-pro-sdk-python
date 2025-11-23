"""Tests for Webhooks asynchronous functionality."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_webhook_model(mocker: "MockerFixture") -> MagicMock:
    """Create a mock webhook model."""
    mock_model = MagicMock()
    mock_model.model_dump_json.return_value = '{"event": "test"}'
    return mock_model


@pytest.mark.asyncio
class TestAsyncWebhooksClient:
    """Test AsyncWebhooksClient operations."""

    async def test_async_webhooks_client_initialization(self) -> None:
        """Test AsyncWebhooksClient initialization."""
        with patch("src.jamf_pro_sdk.clients.webhooks.httpx.AsyncClient") as mock_client:
            from src.jamf_pro_sdk.clients.webhooks import AsyncWebhooksClient

            client = AsyncWebhooksClient(url="https://example.com/webhook", max_concurrency=5)
            assert client.url == "https://example.com/webhook"
            assert client.max_concurrency == 5

    async def test_async_send_webhook(
        self, mock_webhook_model: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """Test async sending a single webhook."""
        with patch("src.jamf_pro_sdk.clients.webhooks.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            from src.jamf_pro_sdk.clients.webhooks import AsyncWebhooksClient

            client = AsyncWebhooksClient(url="https://example.com/webhook")
            response = await client.send_webhook(mock_webhook_model)

            assert response.status_code == 200
            mock_client_instance.post.assert_called_once()

    async def test_async_webhooks_context_manager(self) -> None:
        """Test AsyncWebhooksClient context manager."""
        with patch("src.jamf_pro_sdk.clients.webhooks.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.aclose = AsyncMock()
            mock_client_class.return_value = mock_client_instance

            from src.jamf_pro_sdk.clients.webhooks import AsyncWebhooksClient

            async with AsyncWebhooksClient(url="https://example.com/webhook") as client:
                assert client is not None

            mock_client_instance.aclose.assert_called_once()

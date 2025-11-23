"""Tests for Webhooks synchronous functionality."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

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


class TestWebhooksClient:
    """Test WebhooksClient operations."""

    def test_webhooks_client_initialization(self) -> None:
        """Test WebhooksClient initialization."""
        with patch("src.jamf_pro_sdk.clients.webhooks.httpx.Client") as mock_client:
            from src.jamf_pro_sdk.clients.webhooks import WebhooksClient

            client = WebhooksClient(url="https://example.com/webhook", max_concurrency=5)
            assert client.url == "https://example.com/webhook"
            assert client.max_concurrency == 5

    def test_send_webhook(self, mock_webhook_model: MagicMock, mocker: "MockerFixture") -> None:
        """Test sending a single webhook."""
        with patch("src.jamf_pro_sdk.clients.webhooks.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_client_instance.post.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            from src.jamf_pro_sdk.clients.webhooks import WebhooksClient

            client = WebhooksClient(url="https://example.com/webhook")
            response = client.send_webhook(mock_webhook_model)

            assert response.status_code == 200
            mock_client_instance.post.assert_called_once()

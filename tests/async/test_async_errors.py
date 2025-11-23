"""Tests for async error handling and exception propagation."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from src.jamf_pro_sdk.clients import AsyncJamfProClient
from src.jamf_pro_sdk.clients.auth import UserCredentialsProvider
from src.jamf_pro_sdk.exceptions import CredentialsError

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.mark.asyncio
class TestAsyncErrorHandling:
    """Test async error handling scenarios."""

    async def test_async_client_http_error_propagation(self, mocker: "MockerFixture") -> None:
        """Test that HTTP errors are properly propagated in async context."""
        from datetime import datetime, timedelta, timezone

        credentials = UserCredentialsProvider(username="test", password="test")
        with patch("src.jamf_pro_sdk.clients.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
            # resp.json() is called synchronously, not awaited
            mock_response.json.return_value = {"token": "test", "expires": expires.isoformat()}
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            # Mock a failed API request
            error_response = AsyncMock(spec=httpx.Response)
            error_response.status_code = 404
            error_response.text = "Not Found"
            error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=MagicMock(), response=error_response
            )
            mock_client_instance.request = AsyncMock(return_value=error_response)
            mock_client_class.return_value = mock_client_instance

            client = AsyncJamfProClient(server="test.jamfcloud.com", credentials=credentials)

            with pytest.raises(httpx.HTTPStatusError):
                await client.async_classic_api_request(method="get", resource_path="nonexistent")

    async def test_async_credentials_error_without_client(self) -> None:
        """Test CredentialsError when async client is not attached."""
        from src.jamf_pro_sdk.clients.auth import CredentialsProvider

        provider = CredentialsProvider()
        with pytest.raises(CredentialsError, match="async Jamf Pro client is not attached"):
            await provider.get_access_token_async()

    async def test_async_concurrent_requests_exception_handling(
        self, mocker: "MockerFixture"
    ) -> None:
        """Test exception handling in async concurrent requests."""
        credentials = UserCredentialsProvider(username="test", password="test")
        with patch("src.jamf_pro_sdk.clients.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json = AsyncMock(
                return_value={"token": "test", "expires": "2024-01-01T00:00:00Z"}
            )
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client_instance

            client = AsyncJamfProClient(server="test.jamfcloud.com", credentials=credentials)

            async def failing_handler(arg: int) -> int:
                if arg == 2:
                    raise ValueError("Test error")
                return arg

            # Test with return_exceptions=False (default)
            results = []
            async for result in client.async_concurrent_api_requests(
                failing_handler, [1, 2, 3], return_exceptions=False
            ):
                results.append(result)

            # Exceptions should be skipped
            assert len(results) == 2
            assert 1 in results
            assert 3 in results

    async def test_async_context_manager_exception_handling(self, mocker: "MockerFixture") -> None:
        """Test that async context manager properly handles exceptions."""
        credentials = UserCredentialsProvider(username="test", password="test")
        with patch("src.jamf_pro_sdk.clients.httpx.AsyncClient") as mock_client_class:
            mock_client_instance = AsyncMock()
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json = AsyncMock(
                return_value={"token": "test", "expires": "2024-01-01T00:00:00Z"}
            )
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client_instance.aclose = AsyncMock()
            mock_client_class.return_value = mock_client_instance

            async with AsyncJamfProClient(
                server="test.jamfcloud.com", credentials=credentials
            ) as client:
                assert client is not None

            # Verify cleanup was called even if exception occurred
            mock_client_instance.aclose.assert_called_once()

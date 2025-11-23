"""Tests for async pagination functionality."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from src.jamf_pro_sdk.clients.pro_api.pagination import AsyncPaginator, Page

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_async_api_client(mocker: "MockerFixture") -> MagicMock:
    """Create a mock async API client."""
    mock_client = MagicMock()
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {
        "results": [],
        "page": 0,
        "pageSize": 100,
        "totalCount": 0,
    }
    mock_client.api_request = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.mark.asyncio
class TestAsyncPaginator:
    """Test AsyncPaginator."""

    async def test_async_paginator_initialization(self, mock_async_api_client: MagicMock) -> None:
        """Test AsyncPaginator initialization."""
        paginator = AsyncPaginator(
            api_client=mock_async_api_client,
            resource_path="v1/test",
            return_model=None,
            start_page=0,
            end_page=None,
            page_size=100,
        )
        assert paginator.start_page == 0
        assert paginator.page_size == 100

    async def test_async_paginator_iteration(self, mock_async_api_client: MagicMock) -> None:
        """Test async paginator iteration."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "results": [{"id": "1"}],
            "page": 0,
            "pageSize": 100,
            "totalCount": 1,
        }
        mock_async_api_client.api_request = AsyncMock(return_value=mock_response)

        paginator = AsyncPaginator(
            api_client=mock_async_api_client,
            resource_path="v1/test",
            return_model=None,
        )

        # AsyncPaginator.__call__ is async and returns the async generator
        pages = []
        async_gen = await paginator(return_generator=True)
        async for page in async_gen:
            pages.append(page)

        assert len(pages) == 1
        assert isinstance(pages[0], Page)

    async def test_async_paginator_with_end_page(self, mock_async_api_client: MagicMock) -> None:
        """Test async paginator with end page limit."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "results": [],
            "page": 0,
            "pageSize": 100,
            "totalCount": 0,
        }
        mock_async_api_client.api_request = AsyncMock(return_value=mock_response)

        paginator = AsyncPaginator(
            api_client=mock_async_api_client,
            resource_path="v1/test",
            return_model=None,
            start_page=0,
            end_page=2,
            page_size=100,
        )

        # AsyncPaginator.__call__ is async and returns the async generator
        pages = []
        async_gen = await paginator(return_generator=True)
        async for page in async_gen:
            pages.append(page)

        assert len(pages) <= 3  # pages 0, 1, 2

"""Tests for Pro API asynchronous functionality."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from src.jamf_pro_sdk.clients.pro_api import AsyncProApi
from src.jamf_pro_sdk.clients.pro_api.pagination import FilterField
from src.jamf_pro_sdk.models.pro.computers import Computer

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_async_request_method(mocker: "MockerFixture") -> AsyncMock:
    """Create a mock async request method."""
    return AsyncMock()


@pytest.fixture
def mock_async_concurrent_method(mocker: "MockerFixture") -> MagicMock:
    """Create a mock async concurrent requests method."""
    return AsyncMock()


@pytest.fixture
def async_pro_api(
    mock_async_request_method: MagicMock, mock_async_concurrent_method: MagicMock
) -> AsyncProApi:
    """Create an AsyncProApi instance with mocked methods."""
    return AsyncProApi(mock_async_request_method, mock_async_concurrent_method)


@pytest.mark.asyncio
class TestAsyncProApiComputers:
    """Test async Pro API computer operations."""

    async def test_get_computer_inventory_v1_async(
        self, async_pro_api: AsyncProApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async getting computer inventory."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "results": [{"id": "123", "general": {"name": "Test Computer"}}],
            "page": 0,
            "pageSize": 100,
            "totalCount": 1,
        }
        mock_async_request_method.return_value = mock_response

        computers = await async_pro_api.get_computer_inventory_v1()
        assert isinstance(computers, list)
        assert len(computers) == 1

    async def test_get_computer_inventory_v1_async_with_filter(
        self, async_pro_api: AsyncProApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async getting computer inventory with filter."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "results": [],
            "page": 0,
            "pageSize": 100,
            "totalCount": 0,
        }
        mock_async_request_method.return_value = mock_response

        filter_expr = FilterField("general.name").eq("Test Computer")
        computers = await async_pro_api.get_computer_inventory_v1(filter_expression=filter_expr)
        assert isinstance(computers, list)


@pytest.mark.asyncio
class TestAsyncProApiPagination:
    """Test async Pro API pagination."""

    async def test_async_paginator_iteration(
        self, async_pro_api: AsyncProApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async paginator iteration."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "results": [],
            "page": 0,
            "pageSize": 100,
            "totalCount": 0,
        }
        mock_async_request_method.return_value = mock_response

        # get_computer_inventory_v1 with return_generator=True awaits paginator.__call__
        # which returns an AsyncIterator
        paginator_gen = await async_pro_api.get_computer_inventory_v1(return_generator=True)
        pages = []
        async for page in paginator_gen:
            pages.append(page)

        assert isinstance(pages, list)

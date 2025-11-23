"""Tests for Pro API synchronous functionality."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import httpx
import pytest
from src.jamf_pro_sdk.clients.pro_api import ProApi
from src.jamf_pro_sdk.clients.pro_api.pagination import FilterField, SortField
from src.jamf_pro_sdk.models.pro.computers import Computer

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_request_method(mocker: "MockerFixture") -> MagicMock:
    """Create a mock request method."""
    return MagicMock()


@pytest.fixture
def mock_concurrent_method(mocker: "MockerFixture") -> MagicMock:
    """Create a mock concurrent requests method."""
    return MagicMock()


@pytest.fixture
def pro_api(mock_request_method: MagicMock, mock_concurrent_method: MagicMock) -> ProApi:
    """Create a ProApi instance with mocked methods."""
    return ProApi(mock_request_method, mock_concurrent_method)


class TestProApiComputers:
    """Test Pro API computer operations."""

    def test_get_computer_inventory_v1_default(
        self, pro_api: ProApi, mock_request_method: MagicMock
    ) -> None:
        """Test getting computer inventory with defaults."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "results": [{"id": "123", "general": {"name": "Test Computer"}}],
            "page": 0,
            "pageSize": 100,
            "totalCount": 1,
        }
        mock_request_method.return_value = mock_response

        computers = pro_api.get_computer_inventory_v1()
        assert isinstance(computers, list)
        assert len(computers) == 1

    def test_get_computer_inventory_v1_with_sections(
        self, pro_api: ProApi, mock_request_method: MagicMock
    ) -> None:
        """Test getting computer inventory with specific sections."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "results": [{"id": "123"}],
            "page": 0,
            "pageSize": 100,
            "totalCount": 1,
        }
        mock_request_method.return_value = mock_response

        computers = pro_api.get_computer_inventory_v1(sections=["GENERAL", "HARDWARE"])
        assert len(computers) == 1

    def test_get_computer_inventory_v1_with_filter(
        self, pro_api: ProApi, mock_request_method: MagicMock
    ) -> None:
        """Test getting computer inventory with filter expression."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "results": [],
            "page": 0,
            "pageSize": 100,
            "totalCount": 0,
        }
        mock_request_method.return_value = mock_response

        filter_expr = FilterField("general.name").eq("Test Computer")
        computers = pro_api.get_computer_inventory_v1(filter_expression=filter_expr)
        assert isinstance(computers, list)

    def test_get_computer_inventory_v1_with_sort(
        self, pro_api: ProApi, mock_request_method: MagicMock
    ) -> None:
        """Test getting computer inventory with sort expression."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "results": [],
            "page": 0,
            "pageSize": 100,
            "totalCount": 0,
        }
        mock_request_method.return_value = mock_response

        sort_expr = SortField("general.name").asc()
        computers = pro_api.get_computer_inventory_v1(sort_expression=sort_expr)
        assert isinstance(computers, list)

    def test_get_computer_inventory_v1_with_generator(
        self, pro_api: ProApi, mock_request_method: MagicMock
    ) -> None:
        """Test getting computer inventory as generator."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "results": [],
            "page": 0,
            "pageSize": 100,
            "totalCount": 0,
        }
        mock_request_method.return_value = mock_response

        result = pro_api.get_computer_inventory_v1(return_generator=True)
        assert hasattr(result, "__iter__")

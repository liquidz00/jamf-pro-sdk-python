"""Tests for Classic API asynchronous functionality."""

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from src.jamf_pro_sdk.clients.classic_api import AsyncClassicApi
from src.jamf_pro_sdk.models.classic.advanced_computer_searches import (
    ClassicAdvancedComputerSearch,
    ClassicAdvancedComputerSearchesItem,
)
from src.jamf_pro_sdk.models.classic.categories import ClassicCategoriesItem, ClassicCategory
from src.jamf_pro_sdk.models.classic.computer_groups import ClassicComputerGroup
from src.jamf_pro_sdk.models.classic.packages import ClassicPackage, ClassicPackageItem

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_async_request_method(mocker: "MockerFixture") -> AsyncMock:
    """Create a mock async request method."""
    # Use AsyncMock since the method is awaited
    # When awaited, AsyncMock returns the return_value
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_async_concurrent_method(mocker: "MockerFixture") -> MagicMock:
    """Create a mock async concurrent requests method."""
    # Use MagicMock instead of AsyncMock so we can control the return value directly
    return MagicMock()


@pytest.fixture
def async_classic_api(
    mock_async_request_method: AsyncMock, mock_async_concurrent_method: MagicMock
) -> AsyncClassicApi:
    """Create an AsyncClassicApi instance with mocked methods."""
    return AsyncClassicApi(mock_async_request_method, mock_async_concurrent_method)


@pytest.mark.asyncio
class TestAsyncClassicApiCategories:
    """Test async Classic API category operations."""

    async def test_list_all_categories_async(
        self, async_classic_api: AsyncClassicApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async listing all categories."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "categories": [
                {"id": 1, "name": "Category 1", "priority": 1},
                {"id": 2, "name": "Category 2", "priority": 2},
            ]
        }
        mock_async_request_method.return_value = mock_response

        categories = await async_classic_api.list_all_categories()
        assert len(categories) == 2
        assert isinstance(categories[0], ClassicCategoriesItem)

    async def test_get_category_by_id_async(
        self, async_classic_api: AsyncClassicApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async getting category by ID."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "category": {"id": 1, "name": "Test Category", "priority": 1}
        }
        mock_async_request_method.return_value = mock_response

        category = await async_classic_api.get_category_by_id(1)
        assert isinstance(category, ClassicCategory)
        assert category.id == 1

    async def test_create_category_async(
        self, async_classic_api: AsyncClassicApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async creating a category."""
        mock_response = MagicMock(spec=httpx.Response)
        # The XML should have a root element containing <id>, not root being <id>
        # parse_response_id expects root.find("id") to find a child element
        mock_response.text = '<?xml version="1.0"?><response><id>123</id></response>'
        # Configure AsyncMock to return the response when awaited
        mock_async_request_method.return_value = mock_response

        category = ClassicCategory(id=0, name="New Category", priority=1)
        category_id = await async_classic_api.create_category(category)
        assert category_id == 123
        # Verify the method was called with correct arguments
        mock_async_request_method.assert_called_once()
        call_args = mock_async_request_method.call_args
        assert call_args[1]["method"] == "post"
        assert "categories/id/0" in call_args[1]["resource_path"]


@pytest.mark.asyncio
class TestAsyncClassicApiConcurrentOperations:
    """Test async Classic API concurrent operations."""

    async def test_async_get_computers(
        self, async_classic_api: AsyncClassicApi, mock_async_concurrent_method: MagicMock
    ) -> None:
        """Test async batch computer fetching."""
        from src.jamf_pro_sdk.models.classic.computers import ClassicComputer

        mock_computer = ClassicComputer.model_validate(
            {"general": {"id": 123, "name": "Test Computer"}}
        )

        # Create a proper async generator function
        async def async_computer_generator():
            """Async generator that yields the mock computer."""
            yield mock_computer

        # Mock the concurrent method to return an async generator directly
        # Since concurrent_api_requests is called and should return an AsyncIterator,
        # we set return_value to the async generator function itself
        # When called, it will return the async generator which is iterable with async for
        mock_async_concurrent_method.return_value = async_computer_generator()

        computers = []
        # get_computers is an async generator that calls concurrent_api_requests
        async for computer in async_classic_api.get_computers([123]):
            computers.append(computer)

        assert len(computers) == 1


@pytest.mark.asyncio
class TestAsyncClassicApiComputerGroups:
    """Test async Classic API computer group operations."""

    async def test_list_all_computer_groups_async(
        self, async_classic_api: AsyncClassicApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async listing all computer groups."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "computer_groups": [
                {"id": 1, "name": "Group 1", "is_smart": True},
                {"id": 2, "name": "Group 2", "is_smart": False},
            ]
        }
        mock_async_request_method.return_value = mock_response

        groups = await async_classic_api.list_all_computer_groups()
        assert len(groups) == 2
        assert isinstance(groups[0], ClassicComputerGroup)
        assert groups[0].id == 1

    async def test_get_computer_group_by_id_async(
        self, async_classic_api: AsyncClassicApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async getting computer group by ID."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "computer_group": {
                "id": 1,
                "name": "Test Group",
                "is_smart": True,
                "computers": [{"id": 123, "name": "Computer 1"}],
            }
        }
        mock_async_request_method.return_value = mock_response

        group = await async_classic_api.get_computer_group_by_id(1)
        assert isinstance(group, ClassicComputerGroup)
        assert group.id == 1


@pytest.mark.asyncio
class TestAsyncClassicApiAdvancedComputerSearches:
    """Test async Classic API advanced computer search operations."""

    async def test_list_all_advanced_computer_searches_async(
        self, async_classic_api: AsyncClassicApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async listing all advanced computer searches."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "advanced_computer_searches": [
                {"id": 1, "name": "Search 1"},
                {"id": 2, "name": "Search 2"},
            ]
        }
        mock_async_request_method.return_value = mock_response

        searches = await async_classic_api.list_all_advanced_computer_searches()
        assert len(searches) == 2
        assert isinstance(searches[0], ClassicAdvancedComputerSearchesItem)
        assert searches[0].id == 1

    async def test_get_advanced_computer_search_by_id_async(
        self, async_classic_api: AsyncClassicApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async getting advanced computer search by ID."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "advanced_computer_search": {
                "id": 1,
                "name": "Test Search",
                "computers": [{"id": 123, "name": "Computer 1"}],
            }
        }
        mock_async_request_method.return_value = mock_response

        search = await async_classic_api.get_advanced_computer_search_by_id(1)
        assert isinstance(search, ClassicAdvancedComputerSearch)
        assert search.id == 1


@pytest.mark.asyncio
class TestAsyncClassicApiPackages:
    """Test async Classic API package operations."""

    async def test_list_all_packages_async(
        self, async_classic_api: AsyncClassicApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async listing all packages."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "packages": [
                {"id": 1, "name": "Package 1"},
                {"id": 2, "name": "Package 2"},
            ]
        }
        mock_async_request_method.return_value = mock_response

        packages = await async_classic_api.list_all_packages()
        assert len(packages) == 2
        assert isinstance(packages[0], ClassicPackageItem)
        assert packages[0].id == 1

    async def test_get_package_by_id_async(
        self, async_classic_api: AsyncClassicApi, mock_async_request_method: AsyncMock
    ) -> None:
        """Test async getting package by ID."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "package": {
                "id": 1,
                "name": "Test Package",
                "filename": "test.pkg",
                "category": "Test Category",
            }
        }
        mock_async_request_method.return_value = mock_response

        package = await async_classic_api.get_package_by_id(1)
        assert isinstance(package, ClassicPackage)
        assert package.id == 1
        assert package.name == "Test Package"

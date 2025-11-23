"""Tests for Classic API synchronous functionality."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock

import httpx
import pytest
from src.jamf_pro_sdk.clients.classic_api import ClassicApi
from src.jamf_pro_sdk.models.classic.advanced_computer_searches import (
    ClassicAdvancedComputerSearch,
    ClassicAdvancedComputerSearchesItem,
)
from src.jamf_pro_sdk.models.classic.categories import ClassicCategoriesItem, ClassicCategory
from src.jamf_pro_sdk.models.classic.computer_groups import (
    ClassicComputerGroup,
    ClassicComputerGroupMember,
)
from src.jamf_pro_sdk.models.classic.computers import ClassicComputer, ClassicComputersItem
from src.jamf_pro_sdk.models.classic.packages import ClassicPackage, ClassicPackageItem

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_request_method(mocker: "MockerFixture") -> MagicMock:
    """
    Create a mock request method.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :return: Mock request method
    :rtype: MagicMock
    """
    return MagicMock()


@pytest.fixture
def mock_concurrent_method(mocker: "MockerFixture") -> MagicMock:
    """
    Create a mock concurrent requests method.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :return: Mock concurrent method
    :rtype: MagicMock
    """
    return MagicMock()


@pytest.fixture
def classic_api(mock_request_method: MagicMock, mock_concurrent_method: MagicMock) -> ClassicApi:
    """
    Create a ClassicApi instance with mocked methods.

    :param mock_request_method: Mock request method
    :type mock_request_method: MagicMock
    :param mock_concurrent_method: Mock concurrent method
    :type mock_concurrent_method: MagicMock
    :return: ClassicApi instance
    :rtype: ClassicApi
    """
    return ClassicApi(mock_request_method, mock_concurrent_method)


class TestClassicApiCategories:
    """Test Classic API category operations."""

    def test_list_all_categories(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test listing all categories.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "categories": [
                {"id": 1, "name": "Category 1", "priority": 1},
                {"id": 2, "name": "Category 2", "priority": 2},
            ]
        }
        mock_request_method.return_value = mock_response

        categories = classic_api.list_all_categories()
        assert len(categories) == 2
        assert isinstance(categories[0], ClassicCategoriesItem)
        assert categories[0].id == 1

    def test_get_category_by_id(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test getting category by ID.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "category": {"id": 1, "name": "Test Category", "priority": 1}
        }
        mock_request_method.return_value = mock_response

        category = classic_api.get_category_by_id(1)
        assert isinstance(category, ClassicCategory)
        assert category.id == 1
        assert category.name == "Test Category"

    def test_get_category_by_id_with_model(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test getting category by ID using model instance.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "category": {"id": 1, "name": "Test Category", "priority": 1}
        }
        mock_request_method.return_value = mock_response

        category_item = ClassicCategoriesItem(id=1, name="Test", priority=1)
        category = classic_api.get_category_by_id(category_item)
        assert isinstance(category, ClassicCategory)

    def test_create_category(self, classic_api: ClassicApi, mock_request_method: MagicMock) -> None:
        """
        Test creating a category.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        mock_response = MagicMock(spec=httpx.Response)
        # parse_response_id expects root.find("id") to find a child element
        mock_response.text = '<?xml version="1.0"?><response><id>123</id></response>'
        mock_request_method.return_value = mock_response

        category = ClassicCategory(id=0, name="New Category", priority=1)
        category_id = classic_api.create_category(category)
        assert category_id == 123

    def test_update_category_by_id(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test updating a category.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_request_method.return_value = mock_response

        category = ClassicCategory(id=1, name="Updated Category", priority=2)
        classic_api.update_category_by_id(1, category)
        mock_request_method.assert_called_once()

    def test_delete_category_by_id(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test deleting a category.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_request_method.return_value = mock_response

        classic_api.delete_category_by_id(1)
        mock_request_method.assert_called_once()


class TestClassicApiComputers:
    """Test Classic API computer operations."""

    def test_list_all_computers(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test listing all computers.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "computers": [
                {"id": 1, "name": "Computer 1"},
                {"id": 2, "name": "Computer 2"},
            ]
        }
        mock_request_method.return_value = mock_response

        computers = classic_api.list_all_computers()
        assert len(computers) == 2
        assert isinstance(computers[0], ClassicComputersItem)

    def test_list_all_computers_with_basic_subset(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test listing computers with basic subset.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {"computers": []}
        mock_request_method.return_value = mock_response

        classic_api.list_all_computers(subsets=["basic"])
        call_args = mock_request_method.call_args
        assert "computers/subset/basic" in call_args[1]["resource_path"]

    def test_list_all_computers_invalid_subset(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test listing computers with invalid subset.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        with pytest.raises(ValueError, match="Invalid subset"):
            classic_api.list_all_computers(subsets=["invalid"])

    def test_get_computer_by_id(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test getting computer by ID.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "computer": {
                "general": {
                    "id": 123,
                    "name": "Test Computer",
                    "mac_address": "AA:BB:CC:DD:EE:FF",
                }
            }
        }
        mock_request_method.return_value = mock_response

        computer = classic_api.get_computer_by_id(123)
        assert isinstance(computer, ClassicComputer)
        assert computer.general.id == 123

    def test_get_computer_by_id_with_subsets(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test getting computer by ID with subsets.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {"computer": {"general": {"id": 123}}}
        mock_request_method.return_value = mock_response

        classic_api.get_computer_by_id(123, subsets=["hardware", "software"])
        call_args = mock_request_method.call_args
        assert "subset" in call_args[1]["resource_path"]

    def test_get_computer_by_id_invalid_subsets(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """
        Test getting computer with invalid subsets.

        :param classic_api: ClassicApi instance
        :type classic_api: ClassicApi
        :param mock_request_method: Mock request method
        :type mock_request_method: MagicMock
        """
        with pytest.raises(ValueError, match="Invalid subset"):
            classic_api.get_computer_by_id(123, subsets=["invalid"])


class TestClassicApiComputerGroups:
    """Test Classic API computer group operations."""

    def test_list_all_computer_groups(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """Test listing all computer groups."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "computer_groups": [
                {"id": 1, "name": "Group 1", "is_smart": True},
                {"id": 2, "name": "Group 2", "is_smart": False},
            ]
        }
        mock_request_method.return_value = mock_response

        groups = classic_api.list_all_computer_groups()
        assert len(groups) == 2
        assert isinstance(groups[0], ClassicComputerGroup)
        assert groups[0].id == 1
        assert groups[0].is_smart is True

    def test_get_computer_group_by_id(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """Test getting computer group by ID."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "computer_group": {
                "id": 1,
                "name": "Test Group",
                "is_smart": True,
                "computers": [{"id": 123, "name": "Computer 1"}],
            }
        }
        mock_request_method.return_value = mock_response

        group = classic_api.get_computer_group_by_id(1)
        assert isinstance(group, ClassicComputerGroup)
        assert group.id == 1
        assert group.name == "Test Group"

    def test_create_computer_group(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """Test creating a computer group."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.text = '<?xml version="1.0"?><response><id>456</id></response>'
        mock_request_method.return_value = mock_response

        group = ClassicComputerGroup(id=0, name="New Group", is_smart=False)
        group_id = classic_api.create_computer_group(group)
        assert group_id == 456
        mock_request_method.assert_called_once()

    def test_update_smart_computer_group_by_id(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """Test updating a smart computer group."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_request_method.return_value = mock_response

        group = ClassicComputerGroup(id=1, name="Updated Group", is_smart=True)
        classic_api.update_smart_computer_group_by_id(1, group)
        mock_request_method.assert_called_once()

    def test_update_static_computer_group_membership_by_id(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """Test updating static computer group membership."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_request_method.return_value = mock_response

        classic_api.update_static_computer_group_membership_by_id(
            computer_group_id=1, computers_to_add=[123, 456], computers_to_remove=[789]
        )
        mock_request_method.assert_called_once()


class TestClassicApiAdvancedComputerSearches:
    """Test Classic API advanced computer search operations."""

    def test_list_all_advanced_computer_searches(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """Test listing all advanced computer searches."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "advanced_computer_searches": [
                {"id": 1, "name": "Search 1"},
                {"id": 2, "name": "Search 2"},
            ]
        }
        mock_request_method.return_value = mock_response

        searches = classic_api.list_all_advanced_computer_searches()
        assert len(searches) == 2
        assert isinstance(searches[0], ClassicAdvancedComputerSearchesItem)
        assert searches[0].id == 1

    def test_get_advanced_computer_search_by_id(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """Test getting advanced computer search by ID."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "advanced_computer_search": {
                "id": 1,
                "name": "Test Search",
                "computers": [{"id": 123, "name": "Computer 1"}],
            }
        }
        mock_request_method.return_value = mock_response

        search = classic_api.get_advanced_computer_search_by_id(1)
        assert isinstance(search, ClassicAdvancedComputerSearch)
        assert search.id == 1

    def test_create_advanced_computer_search(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """Test creating an advanced computer search."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.text = '<?xml version="1.0"?><response><id>789</id></response>'
        mock_request_method.return_value = mock_response

        search = ClassicAdvancedComputerSearch(id=0, name="New Search")
        search_id = classic_api.create_advanced_computer_search(search)
        assert search_id == 789


class TestClassicApiPackages:
    """Test Classic API package operations."""

    def test_list_all_packages(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """Test listing all packages."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "packages": [
                {"id": 1, "name": "Package 1"},
                {"id": 2, "name": "Package 2"},
            ]
        }
        mock_request_method.return_value = mock_response

        packages = classic_api.list_all_packages()
        assert len(packages) == 2
        assert isinstance(packages[0], ClassicPackageItem)
        assert packages[0].id == 1

    def test_get_package_by_id(
        self, classic_api: ClassicApi, mock_request_method: MagicMock
    ) -> None:
        """Test getting package by ID."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {
            "package": {
                "id": 1,
                "name": "Test Package",
                "filename": "test.pkg",
                "category": "Test Category",
            }
        }
        mock_request_method.return_value = mock_response

        package = classic_api.get_package_by_id(1)
        assert isinstance(package, ClassicPackage)
        assert package.id == 1
        assert package.name == "Test Package"

    def test_create_package(self, classic_api: ClassicApi, mock_request_method: MagicMock) -> None:
        """Test creating a package."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.text = '<?xml version="1.0"?><response><id>999</id></response>'
        mock_request_method.return_value = mock_response

        package = ClassicPackage(id=0, name="New Package", filename="new.pkg")
        package_id = classic_api.create_package(package)
        assert package_id == 999

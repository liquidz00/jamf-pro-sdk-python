"""Tests for Pro API models."""

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from src.jamf_pro_sdk.models.pro.computers import Computer
from src.jamf_pro_sdk.models.pro.mobile_devices import MobileDevice
from src.jamf_pro_sdk.models.pro.packages import Package

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestComputerModel:
    """Test Computer model."""

    def test_computer_model_initialization(self) -> None:
        """Test Computer model initialization."""
        computer_data = {
            "id": str(uuid4()),
            "general": {
                "name": "Test Computer",
                "udid": str(uuid4()),
                "serialNumber": "TEST123",
            },
        }
        computer = Computer.model_validate(computer_data)
        assert computer.id == computer_data["id"]
        assert computer.general.name == "Test Computer"

    def test_computer_model_serialization(self) -> None:
        """Test Computer model JSON serialization."""
        computer_data = {
            "id": str(uuid4()),
            "general": {"name": "Test Computer", "udid": str(uuid4())},
        }
        computer = Computer.model_validate(computer_data)
        serialized = computer.model_dump_json(exclude_none=True)
        assert "Test Computer" in serialized


class TestMobileDeviceModel:
    """Test MobileDevice model."""

    def test_mobile_device_model_initialization(self) -> None:
        """Test MobileDevice model initialization."""
        device_data = {
            "id": str(uuid4()),
            "general": {
                "name": "Test iPhone",
                "udid": str(uuid4()),
                "serialNumber": "IPHONE123",
            },
        }
        device = MobileDevice.model_validate(device_data)
        assert device.id == device_data["id"]
        assert device.general.name == "Test iPhone"


class TestPackageModel:
    """Test Package model."""

    def test_package_model_initialization(self) -> None:
        """Test Package model initialization."""
        package_data = {
            "id": str(uuid4()),
            "packageName": "Test Package",
            "fileName": "test.pkg",
        }
        package = Package.model_validate(package_data)
        assert package.packageName == "Test Package"
        assert package.fileName == "test.pkg"

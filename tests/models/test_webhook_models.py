"""Tests for Webhook models."""

from ipaddress import IPv4Address
from typing import TYPE_CHECKING

import pytest
from src.jamf_pro_sdk.models.webhooks import (
    ComputerAdded,
    ComputerCheckIn,
    ComputerInventoryCompleted,
    ComputerPolicyFinished,
    ComputerPushCapabilityChanged,
    DeviceAddedToDep,
    JssShutdown,
    JssStartup,
    MobileDeviceCheckIn,
    MobileDeviceEnrolled,
    MobileDevicePushSent,
    MobileDeviceUnEnrolled,
    PushSent,
    RestApiOperation,
    SmartGroupComputerMembershipChange,
    SmartGroupMobileDeviceMembershipChange,
    SmartGroupUserMembershipChange,
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestWebhookData:
    """Test WebhookData base model."""

    def test_webhook_data_validation(self) -> None:
        """Test WebhookData model validation."""
        from src.jamf_pro_sdk.models.webhooks.webhooks import WebhookData

        data = {
            "eventTimestamp": 1234567890,
            "id": 1,
            "name": "Test Webhook",
        }
        webhook_data = WebhookData.model_validate(data)
        assert webhook_data.eventTimestamp == 1234567890
        assert webhook_data.id == 1
        assert webhook_data.name == "Test Webhook"


class TestComputerWebhooks:
    """Test computer-related webhook models."""

    def test_computer_added_validation(self) -> None:
        """Test ComputerAdded model validation."""
        webhook_data = {
            "eventTimestamp": 1234567890,
            "id": 1,
            "name": "Computer Added",
            "webhookEvent": "ComputerAdded",
        }
        event_data = {
            "alternateMacAddress": "00:11:22:33:44:55",
            "building": "Building A",
            "department": "IT",
            "deviceName": "Test Mac",
            "emailAddress": "test@example.com",
            "ipAddress": "192.168.1.100",
            "jssID": 123,
            "macAddress": "AA:BB:CC:DD:EE:FF",
            "model": "MacBook Pro",
            "osBuild": "21G72",
            "osVersion": "12.0",
            "phone": "555-1234",
            "position": "Developer",
            "realName": "Test User",
            "reportedIpAddress": "192.168.1.100",
            "room": "101",
            "serialNumber": "C02XXXXXXHD1",
            "udid": "00000000-0000-0000-0000-000000000000",
            "userDirectoryID": "user123",
            "username": "testuser",
        }
        data = {"webhook": webhook_data, "event": event_data}
        computer_added = ComputerAdded.model_validate(data)
        assert computer_added.webhook.name == "Computer Added"
        assert computer_added.event.serialNumber == "C02XXXXXXHD1"

    def test_computer_check_in_validation(self) -> None:
        """Test ComputerCheckIn model validation."""
        webhook_data = {
            "eventTimestamp": 1234567890,
            "id": 1,
            "name": "Computer Check In",
            "webhookEvent": "ComputerCheckIn",
        }
        computer_data = {
            "alternateMacAddress": "00:11:22:33:44:55",
            "building": "Building A",
            "department": "IT",
            "deviceName": "Test Mac",
            "emailAddress": "test@example.com",
            "ipAddress": "192.168.1.100",
            "jssID": 123,
            "macAddress": "AA:BB:CC:DD:EE:FF",
            "model": "MacBook Pro",
            "osBuild": "21G72",
            "osVersion": "12.0",
            "phone": "555-1234",
            "position": "Developer",
            "realName": "Test User",
            "reportedIpAddress": "192.168.1.100",
            "room": "101",
            "serialNumber": "C02XXXXXXHD1",
            "udid": "00000000-0000-0000-0000-000000000000",
            "userDirectoryID": "user123",
            "username": "testuser",
        }
        event_data = {
            "computer": computer_data,
            "trigger": "SCHEDULED",
            "username": "testuser",
        }
        data = {"webhook": webhook_data, "event": event_data}
        computer_check_in = ComputerCheckIn.model_validate(data)
        assert computer_check_in.webhook.webhookEvent == "ComputerCheckIn"
        assert computer_check_in.event.computer.deviceName == "Test Mac"
        assert computer_check_in.event.trigger == "SCHEDULED"

    def test_computer_inventory_completed_validation(self) -> None:
        """Test ComputerInventoryCompleted model validation."""
        webhook_data = {
            "eventTimestamp": 1234567890,
            "id": 1,
            "name": "Computer Inventory Completed",
            "webhookEvent": "ComputerInventoryCompleted",
        }
        event_data = {
            "alternateMacAddress": "00:11:22:33:44:55",
            "building": "Building A",
            "department": "IT",
            "deviceName": "Test Mac",
            "emailAddress": "test@example.com",
            "ipAddress": "192.168.1.100",
            "jssID": 123,
            "macAddress": "AA:BB:CC:DD:EE:FF",
            "model": "MacBook Pro",
            "osBuild": "21G72",
            "osVersion": "12.0",
            "phone": "555-1234",
            "position": "Developer",
            "realName": "Test User",
            "reportedIpAddress": "192.168.1.100",
            "room": "101",
            "serialNumber": "C02XXXXXXHD1",
            "udid": "00000000-0000-0000-0000-000000000000",
            "userDirectoryID": "user123",
            "username": "testuser",
        }
        data = {"webhook": webhook_data, "event": event_data}
        computer_inventory = ComputerInventoryCompleted.model_validate(data)
        assert computer_inventory.webhook.webhookEvent == "ComputerInventoryCompleted"


class TestMobileDeviceWebhooks:
    """Test mobile device-related webhook models."""

    def test_mobile_device_enrolled_validation(self) -> None:
        """Test MobileDeviceEnrolled model validation."""
        webhook_data = {
            "eventTimestamp": 1234567890,
            "id": 1,
            "name": "Mobile Device Enrolled",
            "webhookEvent": "MobileDeviceEnrolled",
        }
        event_data = {
            "bluetoothMacAddress": "00:11:22:33:44:55",
            "deviceName": "Test iPhone",
            "icciID": "12345678901234567890",
            "imei": "123456789012345",
            "ipAddress": "192.168.1.100",
            "jssID": 456,
            "model": "iPhone",
            "modelDisplay": "iPhone 13",
            "modelIdentifier": "iPhone14,2",
            "modelNumber": "A2482",
            "osBuild": "19A346",
            "osType": "iOS",
            "osVersion": "15.0",
            "product": "iPhone",
            "room": "101",
            "serialNumber": "F2LDXXXXXXHD1",
            "udid": "00000000-0000-0000-0000-000000000001",
            "userDirectoryID": "user123",
            "username": "testuser",
            "version": "15.0",
            "wifiMacAddress": "AA:BB:CC:DD:EE:FF",
        }
        data = {"webhook": webhook_data, "event": event_data}
        mobile_device = MobileDeviceEnrolled.model_validate(data)
        assert mobile_device.webhook.webhookEvent == "MobileDeviceEnrolled"
        assert mobile_device.event.deviceName == "Test iPhone"

    def test_mobile_device_check_in_validation(self) -> None:
        """Test MobileDeviceCheckIn model validation."""
        webhook_data = {
            "eventTimestamp": 1234567890,
            "id": 1,
            "name": "Mobile Device Check In",
            "webhookEvent": "MobileDeviceCheckIn",
        }
        event_data = {
            "bluetoothMacAddress": "00:11:22:33:44:55",
            "deviceName": "Test iPhone",
            "icciID": "12345678901234567890",
            "imei": "123456789012345",
            "ipAddress": "192.168.1.100",
            "jssID": 456,
            "model": "iPhone",
            "modelDisplay": "iPhone 13",
            "modelIdentifier": "iPhone14,2",
            "modelNumber": "A2482",
            "osBuild": "19A346",
            "osType": "iOS",
            "osVersion": "15.0",
            "product": "iPhone",
            "room": "101",
            "serialNumber": "F2LDXXXXXXHD1",
            "udid": "00000000-0000-0000-0000-000000000001",
            "userDirectoryID": "user123",
            "username": "testuser",
            "version": "15.0",
            "wifiMacAddress": "AA:BB:CC:DD:EE:FF",
        }
        data = {"webhook": webhook_data, "event": event_data}
        mobile_device = MobileDeviceCheckIn.model_validate(data)
        assert mobile_device.webhook.webhookEvent == "MobileDeviceCheckIn"


class TestJssWebhooks:
    """Test JSS startup/shutdown webhook models."""

    def test_jss_startup_validation(self) -> None:
        """Test JssStartup model validation."""
        webhook_data = {
            "eventTimestamp": 1234567890,
            "id": 1,
            "name": "JSS Startup",
            "webhookEvent": "JSSStartup",
        }
        event_data = {
            "hostAddress": "192.168.1.1",
            "institution": "Test Institution",
            "isClusterMaster": True,
            "jssUrl": "https://test.jamfcloud.com",
            "webApplicationPath": "/",
        }
        data = {"webhook": webhook_data, "event": event_data}
        jss_startup = JssStartup.model_validate(data)
        assert jss_startup.webhook.webhookEvent == "JSSStartup"
        assert jss_startup.event.jssUrl == "https://test.jamfcloud.com"

    def test_jss_shutdown_validation(self) -> None:
        """Test JssShutdown model validation."""
        webhook_data = {
            "eventTimestamp": 1234567890,
            "id": 1,
            "name": "JSS Shutdown",
            "webhookEvent": "JSSShutdown",
        }
        event_data = {
            "hostAddress": "192.168.1.1",
            "institution": "Test Institution",
            "isClusterMaster": False,
            "jssUrl": "https://test.jamfcloud.com",
            "webApplicationPath": "/",
        }
        data = {"webhook": webhook_data, "event": event_data}
        jss_shutdown = JssShutdown.model_validate(data)
        assert jss_shutdown.webhook.webhookEvent == "JSSShutdown"


class TestSmartGroupWebhooks:
    """Test smart group membership change webhook models."""

    def test_smart_group_computer_membership_change_validation(self) -> None:
        """Test SmartGroupComputerMembershipChange model validation."""
        webhook_data = {
            "eventTimestamp": 1234567890,
            "id": 1,
            "name": "Smart Group Computer Membership Change",
            "webhookEvent": "SmartGroupComputerMembershipChange",
        }
        event_data = {
            "computer": True,
            "groupAddedDevices": [{"id": 123, "name": "Computer 1"}],
            "groupAddedDevicesIds": [123],
            "groupRemovedDevices": [{"id": 456, "name": "Computer 2"}],
            "groupRemovedDevicesIds": [456],
            "jssid": 1,
            "name": "Test Smart Group",
            "smartGroup": True,
        }
        data = {"webhook": webhook_data, "event": event_data}
        smart_group = SmartGroupComputerMembershipChange.model_validate(data)
        assert smart_group.webhook.webhookEvent == "SmartGroupComputerMembershipChange"
        assert len(smart_group.event.groupAddedDevices) == 1
        assert len(smart_group.event.groupRemovedDevices) == 1
        assert smart_group.event.computer is True


class TestWebhookSerialization:
    """Test webhook model serialization."""

    def test_computer_added_serialization(self) -> None:
        """Test ComputerAdded model JSON serialization."""
        webhook_data = {
            "eventTimestamp": 1234567890,
            "id": 1,
            "name": "Computer Added",
            "webhookEvent": "ComputerAdded",
        }
        event_data = {
            "alternateMacAddress": "00:11:22:33:44:55",
            "building": "Building A",
            "department": "IT",
            "deviceName": "Test Mac",
            "emailAddress": "test@example.com",
            "ipAddress": "192.168.1.100",
            "jssID": 123,
            "macAddress": "AA:BB:CC:DD:EE:FF",
            "model": "MacBook Pro",
            "osBuild": "21G72",
            "osVersion": "12.0",
            "phone": "555-1234",
            "position": "Developer",
            "realName": "Test User",
            "reportedIpAddress": "192.168.1.100",
            "room": "101",
            "serialNumber": "C02XXXXXXHD1",
            "udid": "00000000-0000-0000-0000-000000000000",
            "userDirectoryID": "user123",
            "username": "testuser",
        }
        data = {"webhook": webhook_data, "event": event_data}
        computer_added = ComputerAdded.model_validate(data)
        serialized = computer_added.model_dump_json(exclude_none=True)
        assert "ComputerAdded" in serialized
        assert "C02XXXXXXHD1" in serialized

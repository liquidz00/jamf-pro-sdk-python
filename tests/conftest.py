# Configure pytest-asyncio - must be before any imports
pytest_plugins = ("pytest_asyncio",)

from typing import TYPE_CHECKING, Any

import pytest
from src.jamf_pro_sdk.models.classic.categories import ClassicCategory
from src.jamf_pro_sdk.models.classic.computer_groups import ClassicComputerGroup
from src.jamf_pro_sdk.models.classic.computers import (
    ClassicComputer,
    ClassicComputerExtensionAttribute,
    ClassicComputerGeneralRemoteManagement,
)
from src.jamf_pro_sdk.models.classic.network_segments import ClassicNetworkSegment

if TYPE_CHECKING:
    pass


# Classic API Test Data Fixtures
@pytest.fixture
def category_json_data() -> dict[str, Any]:
    """
    Sample category JSON payload for testing.

    :return: dictionary containing category test data
    :rtype: dict[str, Any]
    """
    return {"category": {"id": 1, "name": "Test Category", "priority": 1}}


@pytest.fixture
def computer_group_json_data() -> dict[str, Any]:
    """
    Sample computer group JSON payload for testing.

    :return: dictionary containing computer group test data
    :rtype: dict[str, Any]
    """
    return {
        "computer_group": {
            "id": 1,
            "name": "All Managed Clients",
            "is_smart": True,
            "site": {"id": -1, "name": "None"},
            "criteria": [
                {
                    "name": "Operating System",
                    "priority": 0,
                    "and_or": "and",
                    "search_type": "not like",
                    "value": "server",
                    "opening_paren": False,
                    "closing_paren": False,
                },
                {
                    "name": "Application Title",
                    "priority": 1,
                    "and_or": "and",
                    "search_type": "is not",
                    "value": "Server.app",
                    "opening_paren": False,
                    "closing_paren": False,
                },
            ],
            "computers": [
                {
                    "id": 123,
                    "name": "Peccy's MacBook Pro",
                    "mac_address": "AA:BB:CC:DD:EE:FF",
                    "alt_mac_address": "",
                    "serial_number": "C02XXXXXXHD1",
                },
                {
                    "id": 456,
                    "name": "Jeff's MacBook Pro",
                    "mac_address": "00:11:22:33:44:55",
                    "alt_mac_address": "",
                    "serial_number": "C02XXXXXXHD2",
                },
            ],
        }
    }


@pytest.fixture
def computer_json_data() -> dict[str, Any]:
    """
    Sample computer JSON payload for testing.

    :return: dictionary containing computer test data
    :rtype: dict[str, Any]
    """
    return {
        "computer": {
            "general": {
                "id": 123,
                "name": "Admin's MacBook Pro",
                "network_adapter_type": "IEEE80211",
                "mac_address": "A0:B1:C2:D3:E4:F5",
                "alt_network_adapter_type": "Ethernet",
                "alt_mac_address": "F9:E8:D7:C6:B5:A4",
                "ip_address": "10.1.100.101",
                "last_reported_ip": "192.168.100.101",
                "serial_number": "ABCDE12345",
                "udid": "0285E974-2664-4414-BDD3-DC4C93A0408F",
                "jamf_version": "10.42.1",
                "platform": "Mac",
                "barcode_1": "",
                "barcode_2": "",
                "asset_tag": "",
                "remote_management": {
                    "managed": True,
                    "management_username": "admin",
                    "management_password_sha256": "********************",
                },
                "supervised": True,
                "mdm_capable": True,
                # "mdm_capable_users": {"mdm_capable_user": "admin"},
                "mdm_capable_users": {},
                "management_status": {
                    "enrolled_via_dep": True,
                    "user_approved_enrollment": True,
                    "user_approved_mdm": True,
                },
                "report_date": "2022-12-22 21:31:48",
                "report_date_epoch": 1671744708190,
                "report_date_utc": "2022-12-22T21:31:48.190+0000",
                "last_contact_time": "2022-12-22 22:36:30",
                "last_contact_time_epoch": 1671748590710,
                "last_contact_time_utc": "2022-12-22T22:36:30.710+0000",
                "initial_entry_date": "2022-08-24",
                "initial_entry_date_epoch": 1661378276032,
                "initial_entry_date_utc": "2022-08-24T21:57:56.032+0000",
                "last_cloud_backup_date_epoch": 0,
                "last_cloud_backup_date_utc": "",
                "last_enrolled_date_epoch": 1661378431943,
                "last_enrolled_date_utc": "2022-08-24T22:00:31.943+0000",
                "mdm_profile_expiration_epoch": 1724536807000,
                "mdm_profile_expiration_utc": "2024-08-24T22:00:07.000+0000",
                "distribution_point": "",
                "sus": "",
                "site": {"id": -1, "name": "None"},
                "itunes_store_account_is_active": False,
            },
            "location": {
                "username": "admin",
                "realname": "Full, Admin",
                "real_name": "Full, Admin",
                "email_address": "admin@my.org",
                "position": "Administrator",
                "phone": "",
                "phone_number": "",
                "department": "",
                "building": "",
                "room": "",
            },
            "purchasing": {
                "is_purchased": True,
                "is_leased": False,
                "po_number": "",
                "vendor": "",
                "applecare_id": "",
                "purchase_price": "",
                "purchasing_account": "",
                "po_date": "",
                "po_date_epoch": 0,
                "po_date_utc": "",
                "warranty_expires": "",
                "warranty_expires_epoch": 0,
                "warranty_expires_utc": "",
                "lease_expires": "",
                "lease_expires_epoch": 0,
                "lease_expires_utc": "",
                "life_expectancy": 0,
                "purchasing_contact": "",
                "os_applecare_id": "",
                "os_maintenance_expires": "",
                "attachments": [],
            },
            "peripherals": [],
            "hardware": {
                "make": "Apple",
                "model": "MacBook Pro (14-inch, 2021)",
                "model_identifier": "MacBookPro18,3",
                "os_name": "macOS",
                "os_version": "12.6.1",
                "os_build": "21G217",
                "software_update_device_id": "J314sAP",
                "active_directory_status": "ldap.my.org",
                "service_pack": "",
                "processor_type": "Apple M1 Pro",
                "is_apple_silicon": True,
                "processor_architecture": "arm64",
                "processor_speed": 0,
                "processor_speed_mhz": 0,
                "number_processors": 1,
                "number_cores": 10,
                "total_ram": 32768,
                "total_ram_mb": 32768,
                "boot_rom": "8419.41.10",
                "bus_speed": 0,
                "bus_speed_mhz": 0,
                "battery_capacity": 1,
                "cache_size": 0,
                "cache_size_kb": 0,
                "available_ram_slots": 0,
                "optical_drive": "",
                "nic_speed": "10/100/1000",
                "smc_version": "",
                "ble_capable": False,
                "supports_ios_app_installs": True,
                "sip_status": "Enabled",
                "gatekeeper_status": "App Store and identified developers",
                "xprotect_version": "2165",
                "institutional_recovery_key": "Not Present",
                "disk_encryption_configuration": "",
                "filevault2_users": ["admin"],
                "storage": [
                    {
                        "disk": "disk0",
                        "model": "APPLE SSD AP0512R",
                        "revision": "873.40.4",
                        "serial_number": "1ba026db1424e123",
                        "size": 500277,
                        "drive_capacity_mb": 500277,
                        "connection_type": "NO",
                        "smart_status": "Verified",
                        "partitions": [
                            {
                                "name": "Macintosh HD (Boot Partition)",
                                "size": 494384,
                                "type": "boot",
                                "partition_capacity_mb": 494384,
                                "percentage_full": 5,
                                "available_mb": 340407,
                                "filevault_status": "Encrypted",
                                "filevault_percent": 100,
                                "filevault2_status": "Encrypted",
                                "filevault2_percent": 100,
                                "boot_drive_available_mb": 340407,
                                "lvgUUID": "",
                                "lvUUID": "",
                                "pvUUID": "",
                            },
                        ],
                    }
                ],
                "mapped_printers": [],
            },
            "certificates": [
                {
                    "common_name": "JSS Built-in Certificate Authority",
                    "identity": False,
                    "expires_utc": "2031-04-05T21:49:19.000+0000",
                    "expires_epoch": 1933192159000,
                    "name": "",
                },
            ],
            "security": {
                "activation_lock": False,
                "recovery_lock_enabled": False,
                "secure_boot_level": "full",
                "external_boot_level": "allowed",
                "firewall_enabled": False,
            },
            "software": {
                "unix_executables": [],
                "licensed_software": [],
                "installed_by_casper": [],
                "installed_by_installer_swu": [],
                "cached_by_casper": [],
                "available_software_updates": [],
                "available_updates": {},
                "running_services": [],
                "applications": [
                    {
                        "name": "App Store.app",
                        "path": "/System/Applications/App Store.app",
                        "version": "3.0",
                        "bundle_id": "com.apple.AppStore",
                    },
                ],
                "fonts": [],
                "plugins": [],
            },
            "extension_attributes": [
                {
                    "id": 168,
                    "name": "Find My Mac Enabled",
                    "type": "String",
                    "multi_value": False,
                    "value": "FALSE",
                },
            ],
            "groups_accounts": {
                "computer_group_memberships": [
                    "Group 1",
                    "Group 2",
                ],
                "local_accounts": [
                    {
                        "name": "admin",
                        "realname": "admin",
                        "uid": "502",
                        "home": "/Users/admin",
                        "home_size": "-1MB",
                        "home_size_mb": -1,
                        "administrator": True,
                        "filevault_enabled": True,
                    },
                ],
                "user_inventories": {
                    "disable_automatic_login": True,
                    "user": {
                        "username": "oscar",
                        "password_history_depth": "",
                        "password_min_length": "4",
                        "password_max_age": "",
                        "password_min_complex_characters": "",
                        "password_require_alphanumeric": "false",
                    },
                },
            },
            "iphones": [],
            "configuration_profiles": [
                {"id": 101, "name": "", "uuid": "", "is_removable": False},
            ],
        }
    }


@pytest.fixture
def network_segment_json_data() -> dict[str, Any]:
    """Sample network segment JSON payload for testing."""
    return {
        "network_segment": {
            "id": 1,
            "name": "Test Network",
            "starting_address": "192.168.1.31",
            "ending_address": "192.168.7.255",
            "distribution_point": "Cloud Distribution Point",
            "url": "https://use1-jcds.services.jamfcloud.com/download/66d8960449b44a668c38e4dddbe094d7",
            "building": "Test Building",
            "department": "Test Department",
        }
    }


@pytest.fixture
def computer_xml_output() -> str:
    """Expected XML output for computer model testing."""
    from tests.utils import remove_whitespaces_newlines

    return remove_whitespaces_newlines(
        """<?xml version="1.0" encoding="UTF-8" ?>
<computer>
    <general>
        <id>123</id>
        <remote_management>
            <management_username>admin</management_username>
            <management_password>p@ssw0rd!</management_password>
        </remote_management>
    </general>
    <location>
        <username>oscar</username>
    </location>
</computer>"""
    )


# Classic API Model Instance Fixtures
@pytest.fixture
def classic_category(category_json_data: dict[str, Any]) -> ClassicCategory:
    """Pre-instantiated ClassicCategory model for testing."""
    return ClassicCategory.model_validate(category_json_data["category"])


@pytest.fixture
def classic_computer_group(
    computer_group_json_data: dict[str, Any],
) -> ClassicComputerGroup:
    """Pre-instantiated ClassicComputerGroup model for testing."""
    return ClassicComputerGroup.model_validate(computer_group_json_data["computer_group"])


@pytest.fixture
def classic_computer(computer_json_data: dict[str, Any]) -> ClassicComputer:
    """Pre-instantiated ClassicComputer model for testing."""
    return ClassicComputer.model_validate(computer_json_data["computer"])


@pytest.fixture
def classic_network_segment(
    network_segment_json_data: dict[str, Any],
) -> ClassicNetworkSegment:
    """Pre-instantiated ClassicNetworkSegment model for testing."""
    return ClassicNetworkSegment.model_validate(network_segment_json_data["network_segment"])


# Utility Model Fixtures
@pytest.fixture
def classic_computer_extension_attribute() -> ClassicComputerExtensionAttribute:
    """Pre-instantiated ClassicComputerExtensionAttribute for testing."""
    ea = ClassicComputerExtensionAttribute()
    ea.id = 1
    ea.value = "foo"
    return ea


@pytest.fixture
def classic_computer_remote_management() -> ClassicComputerGeneralRemoteManagement:
    """Pre-instantiated ClassicComputerGeneralRemoteManagement for testing."""
    rm = ClassicComputerGeneralRemoteManagement()
    rm.management_username = "admin"
    rm.management_password = "p@ssw0rd!"
    return rm

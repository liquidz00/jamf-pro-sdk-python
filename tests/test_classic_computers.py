import json
from typing import TYPE_CHECKING

from deepdiff import DeepDiff
from src.jamf_pro_sdk.models.classic.computers import (
    ClassicComputer,
    ClassicComputerGroupsAccountsUserInventoriesUser,
)

if TYPE_CHECKING:
    from src.jamf_pro_sdk.models.classic.computers import (
        ClassicComputerExtensionAttribute,
        ClassicComputerGeneralRemoteManagement,
    )

from typing import Any


def test_computer_model_parsing(classic_computer: "ClassicComputer") -> None:
    """Verify select attributes across the Computer model."""

    assert classic_computer.general is not None  # mypy
    assert classic_computer.general.id == 123

    assert classic_computer.general.remote_management is not None  # mypy
    assert classic_computer.general.remote_management.management_username == "admin"

    assert classic_computer.location is not None  # mypy
    assert classic_computer.location.username == "admin"

    assert classic_computer.purchasing is not None  # mypy
    assert classic_computer.purchasing.is_purchased is True

    assert classic_computer.hardware is not None  # mypy
    assert classic_computer.hardware.model == "MacBook Pro (14-inch, 2021)"
    assert classic_computer.hardware.model_identifier == "MacBookPro18,3"

    assert classic_computer.hardware.filevault2_users is not None  # mypy
    assert classic_computer.hardware.filevault2_users[0] == "admin"

    assert classic_computer.hardware.storage is not None  # mypy
    assert classic_computer.hardware.storage[0].smart_status == "Verified"

    assert classic_computer.hardware.storage[0].partitions is not None  # mypy
    assert classic_computer.hardware.storage[0].partitions[0].size == 494384

    assert classic_computer.certificates is not None  # mypy
    assert classic_computer.certificates[0].common_name == "JSS Built-in Certificate Authority"

    assert classic_computer.security is not None  # mypy
    assert classic_computer.security.activation_lock is False

    assert classic_computer.software is not None  # mypy
    assert classic_computer.software.applications is not None  # mypy
    assert classic_computer.software.applications[0].bundle_id == "com.apple.AppStore"

    assert classic_computer.extension_attributes is not None  # mypy
    assert classic_computer.extension_attributes[0].id == 168

    assert classic_computer.groups_accounts is not None  # mypy
    assert classic_computer.groups_accounts.computer_group_memberships is not None  # mypy
    assert "Group 2" in classic_computer.groups_accounts.computer_group_memberships

    assert classic_computer.groups_accounts.local_accounts is not None  # mypy
    assert classic_computer.groups_accounts.local_accounts[0].uid == "502"
    assert classic_computer.groups_accounts.local_accounts[0].administrator is True

    assert classic_computer.groups_accounts.user_inventories is not None  # mypy
    assert classic_computer.groups_accounts.user_inventories.disable_automatic_login is True

    assert isinstance(
        classic_computer.groups_accounts.user_inventories.user,
        ClassicComputerGroupsAccountsUserInventoriesUser,
    )  # mypy
    # assert classic_computer.groups_accounts.user_inventories.user.username == "oscar"

    assert classic_computer.configuration_profiles is not None  # mypy
    assert classic_computer.configuration_profiles[0].id == 101


def test_computer_model_construct_from_dict() -> None:
    """Test constructing a ClassicComputer from a minimal dictionary."""
    computer = ClassicComputer.model_validate(
        {"general": {"id": 123}, "location": {"username": "oscar"}}
    )

    assert computer.general is not None  # mypy
    assert computer.general.id == 123

    assert computer.location is not None  # mypy
    assert computer.location.username == "oscar"

    computer_dict = computer.model_dump(exclude_none=True)

    assert computer_dict["general"]["id"] == 123
    assert computer_dict["location"]["username"] == "oscar"


def test_computer_model_construct_attrs(
    classic_computer_extension_attribute: "ClassicComputerExtensionAttribute",
) -> None:
    """Test constructing a ClassicComputer with attributes."""
    computer = ClassicComputer()

    assert computer.general is not None  # mypy
    computer.general.id = 123

    assert computer.extension_attributes is not None  # mypy
    computer.extension_attributes.append(classic_computer_extension_attribute)

    assert computer.general.id == 123
    assert computer.extension_attributes[0].id == 1
    assert computer.extension_attributes[0].value == "foo"

    computer_dict = computer.model_dump(exclude_none=True)

    assert computer_dict["general"]["id"] == 123
    assert computer_dict["extension_attributes"][0] == {"id": 1, "value": "foo"}


def test_computer_model_json_output_matches_input(
    classic_computer: "ClassicComputer", computer_json_data: "dict[str, Any]"
) -> None:
    """Test that serialized JSON output matches original input."""
    serialized_output = json.loads(classic_computer.model_dump_json(exclude_none=True))

    diff = DeepDiff(computer_json_data["computer"], serialized_output, ignore_order=True)

    assert not diff


def test_computer_xml_output_matches_expected(
    classic_computer_remote_management: "ClassicComputerGeneralRemoteManagement",
    computer_xml_output: str,
) -> None:
    """Test that XML output matches expected format."""
    computer = ClassicComputer()

    assert computer.general is not None  # mypy
    computer.general.id = 123

    assert computer.location is not None  # mypy
    computer.location.username = "oscar"

    computer.general.remote_management = classic_computer_remote_management

    assert computer.xml() == computer_xml_output

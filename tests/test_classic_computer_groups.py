import json
from typing import TYPE_CHECKING

from deepdiff import DeepDiff

if TYPE_CHECKING:
    from src.jamf_pro_sdk.models.classic.computer_groups import ClassicComputerGroup

from typing import Any, Dict


def test_computer_group_model_parsing(
    classic_computer_group: "ClassicComputerGroup",
) -> None:
    """Verify select attributes across the ComputerGroup model."""
    assert classic_computer_group is not None  # mypy
    assert classic_computer_group.criteria is not None  # mypy
    assert classic_computer_group.computers is not None  # mypy

    assert classic_computer_group.id == 1
    assert classic_computer_group.is_smart is True

    assert len(classic_computer_group.criteria) == 2
    assert len(classic_computer_group.computers) == 2

    assert classic_computer_group.criteria[0].name == "Operating System"
    assert classic_computer_group.criteria[0].search_type == "not like"
    assert classic_computer_group.criteria[0].value == "server"

    assert classic_computer_group.criteria[1].priority == 1
    assert classic_computer_group.criteria[1].and_or == "and"
    assert classic_computer_group.criteria[1].opening_paren is False

    assert classic_computer_group.computers[0].id == 123
    assert classic_computer_group.computers[0].name == "Peccy's MacBook Pro"

    assert classic_computer_group.computers[1].id == 456
    assert classic_computer_group.computers[1].mac_address == "00:11:22:33:44:55"


def test_computer_group_model_json_output_matches_input(
    classic_computer_group: "ClassicComputerGroup",
    computer_group_json_data: "Dict[str, Any]",
) -> None:
    """Test that serialized JSON output matches original input."""
    serialized_output = json.loads(classic_computer_group.model_dump_json(exclude_none=True))

    diff = DeepDiff(
        computer_group_json_data["computer_group"], serialized_output, ignore_order=True
    )

    assert not diff

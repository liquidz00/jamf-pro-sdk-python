import json
from typing import TYPE_CHECKING

from deepdiff import DeepDiff

if TYPE_CHECKING:
    from src.jamf_pro_sdk.models.classic.categories import ClassicCategory

from typing import Any, Dict


def test_category_model_parsings(classic_category: "ClassicCategory") -> None:
    """Verify select attributes across the Category model."""
    assert classic_category is not None  # mypy
    assert classic_category.name == "Test Category"
    assert classic_category.priority == 1
    assert classic_category.id == 1


def test_category_model_json_output_matches_input(
    classic_category: "ClassicCategory", category_json_data: "Dict[str, Any]"
) -> None:
    """Test that serialized JSON output matches original input."""
    serialized_output = json.loads(classic_category.model_dump_json(exclude_none=True))

    diff = DeepDiff(category_json_data["category"], serialized_output, ignore_order=True)

    assert not diff

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pytest import raises
from src.jamf_pro_sdk.models.classic import convert_datetime_to_jamf_iso, remove_fields

if TYPE_CHECKING:
    from typing import Any


def test_convert_datetime_to_jamf_iso() -> None:
    """Test conversion of datetime to Jamf ISO format."""
    dt = datetime(2023, 1, 1, 12, 30, 1, 321000, tzinfo=timezone.utc)
    assert convert_datetime_to_jamf_iso(dt) == "2023-01-01T12:30:01.321+0000"


def test_convert_datetime_to_jamf_iso_no_tz() -> None:
    """Test that datetime without timezone raises ValueError."""
    dt = datetime(2023, 1, 1, 12, 30, 1, 321000)
    with raises(ValueError):
        convert_datetime_to_jamf_iso(dt)


def test_remove_fields() -> None:
    """Test removal of empty fields from nested dictionaries."""
    data: dict[str, Any] = {
        "general": {"id": 123, "remote_management": {}},
        "location": {},
        "hardware": {
            "filevault2_users": ["admin"],
        },
        "extension_attributes": [{}, {"id": 1, "value": "foo"}],
        "certificates": [],
    }

    cleaned_data = remove_fields(data)

    assert cleaned_data == {
        "general": {"id": 123},
        "hardware": {
            "filevault2_users": ["admin"],
        },
        "extension_attributes": [{"id": 1, "value": "foo"}],
    }

"""Tests for exception classes."""

from typing import TYPE_CHECKING

import pytest
from src.jamf_pro_sdk.exceptions import CredentialsError, JamfProSdkException

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestJamfProSdkException:
    """Test JamfProSdkException."""

    def test_jamf_pro_sdk_exception_initialization(self) -> None:
        """Test JamfProSdkException initialization."""
        exception = JamfProSdkException("Test error")
        assert str(exception) == "Test error"
        assert isinstance(exception, Exception)

    def test_jamf_pro_sdk_exception_inheritance(self) -> None:
        """Test JamfProSdkException inheritance."""
        exception = JamfProSdkException("Test")
        assert isinstance(exception, Exception)


class TestCredentialsError:
    """Test CredentialsError."""

    def test_credentials_error_initialization(self) -> None:
        """Test CredentialsError initialization."""
        error = CredentialsError("Invalid credentials")
        assert str(error) == "Invalid credentials"
        assert isinstance(error, JamfProSdkException)

    def test_credentials_error_inheritance(self) -> None:
        """Test CredentialsError inheritance."""
        error = CredentialsError("Test")
        assert isinstance(error, JamfProSdkException)
        assert isinstance(error, Exception)

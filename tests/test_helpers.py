"""Tests for helper functions."""

import logging
import sys
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from src.jamf_pro_sdk.helpers import logger_quick_setup

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestLoggerQuickSetup:
    """Test logger_quick_setup function."""

    def test_logger_quick_setup_info_level(self) -> None:
        """Test logger setup with INFO level."""
        logger_quick_setup(level=logging.INFO)
        logger = logging.getLogger("jamf_pro_sdk")
        assert logger.level == logging.INFO

    def test_logger_quick_setup_debug_level(self) -> None:
        """Test logger setup with DEBUG level."""
        logger_quick_setup(level=logging.DEBUG)
        logger = logging.getLogger("jamf_pro_sdk")
        assert logger.level == logging.DEBUG

    def test_logger_quick_setup_debug_configures_urllib3(self) -> None:
        """Test that DEBUG level also configures urllib3 logger."""
        logger_quick_setup(level=logging.DEBUG)
        urllib3_logger = logging.getLogger("urllib3")
        assert urllib3_logger.level == logging.DEBUG

    def test_logger_quick_setup_adds_handler(self) -> None:
        """Test that logger setup adds a handler."""
        logger_quick_setup(level=logging.INFO)
        logger = logging.getLogger("jamf_pro_sdk")
        assert len(logger.handlers) > 0
        assert isinstance(logger.handlers[0], logging.StreamHandler)

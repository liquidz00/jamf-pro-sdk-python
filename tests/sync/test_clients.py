"""Tests for JamfProClient synchronous functionality."""

import concurrent.futures
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest
from src.jamf_pro_sdk.clients import JamfProClient
from src.jamf_pro_sdk.clients.auth import UserCredentialsProvider
from src.jamf_pro_sdk.models.client import Schemes, SessionConfig

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_credentials() -> UserCredentialsProvider:
    """
    Create a mock credentials provider.

    :return: UserCredentialsProvider instance
    :rtype: UserCredentialsProvider
    """
    return UserCredentialsProvider(username="test_user", password="test_pass")


@pytest.fixture
def mock_token_response() -> dict:
    """
    Create a mock token response.

    :return: Token response dictionary
    :rtype: dict
    """
    from datetime import datetime, timedelta, timezone

    expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
    return {
        "token": "mock_token_12345",
        "expires": expires.isoformat(),
    }


@pytest.fixture
def mock_httpx_client(mocker: "MockerFixture") -> MagicMock:
    """
    Create a mock httpx.Client.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :return: Mock httpx.Client
    :rtype: MagicMock
    """
    mock_client = MagicMock(spec=httpx.Client)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"token": "mock_token", "expires": "2024-01-01T00:00:00Z"}
    mock_response.raise_for_status = Mock()
    mock_client.request.return_value = mock_response
    mock_client.post.return_value = mock_response
    return mock_client


class TestJamfProClientInitialization:
    """Test JamfProClient initialization."""

    def test_client_initialization_defaults(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """
        Test client initialization with default parameters.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        with patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            client = JamfProClient(server="test.jamfcloud.com", credentials=mock_credentials)

            assert client.base_server_url == "https://test.jamfcloud.com:443"
            assert client.session_config.max_concurrency == 5
            assert client.session_config.verify is True
            assert client.session_config.scheme == Schemes.https
            assert client.classic_api is not None
            assert client.pro_api is not None

    def test_client_initialization_custom_port(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """
        Test client initialization with custom port.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        with patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            client = JamfProClient(
                server="test.jamfcloud.com", credentials=mock_credentials, port=8443
            )

            assert client.base_server_url == "https://test.jamfcloud.com:8443"

    def test_client_initialization_custom_session_config(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """
        Test client initialization with custom session config.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        with patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            session_config = SessionConfig(
                timeout=30, max_concurrency=10, return_exceptions=False, verify=False
            )
            client = JamfProClient(
                server="test.jamfcloud.com",
                credentials=mock_credentials,
                session_config=session_config,
            )

            assert client.session_config.timeout == 30
            assert client.session_config.max_concurrency == 10
            assert client.session_config.return_exceptions is False
            assert client.session_config.verify is False

    def test_client_initialization_http_scheme(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """
        Test client initialization with HTTP scheme.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        with patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            session_config = SessionConfig(scheme=Schemes.http)
            client = JamfProClient(
                server="test.jamfcloud.com",
                credentials=mock_credentials,
                session_config=session_config,
            )

            assert client.base_server_url == "http://test.jamfcloud.com:443"


class TestJamfProClientSessionSetup:
    """Test JamfProClient session setup."""

    def test_session_setup_with_timeout(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """
        Test session setup with timeout configuration.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        with patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            session_config = SessionConfig(timeout=60)
            client = JamfProClient(
                server="test.jamfcloud.com",
                credentials=mock_credentials,
                session_config=session_config,
            )

            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert isinstance(call_kwargs["timeout"], httpx.Timeout)
            # httpx.Timeout stores timeout values in connect, read, write, pool attributes
            # When created with a single value, all timeouts are set to that value
            assert call_kwargs["timeout"].connect == 60

    def test_session_setup_without_timeout(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """
        Test session setup without timeout configuration.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        with patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            client = JamfProClient(server="test.jamfcloud.com", credentials=mock_credentials)

            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["timeout"] is None

    def test_session_setup_with_cookies(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture", tmp_path: Path
    ) -> None:
        """
        Test session setup with cookie file.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        :param tmp_path: Temporary directory path
        :type tmp_path: Path
        """
        cookie_file = tmp_path / "cookies.txt"
        cookie_file.write_text(
            "#HttpOnly_test.jamfcloud.com\tFALSE\t/\tFALSE\t0\tcookie_name\tcookie_value\n"
        )

        with patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            session_config = SessionConfig(cookie=str(cookie_file))
            client = JamfProClient(
                server="test.jamfcloud.com",
                credentials=mock_credentials,
                session_config=session_config,
            )

            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["cookies"] == {"cookie_name": "cookie_value"}

    def test_session_setup_with_ca_cert_bundle(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture", tmp_path: Path
    ) -> None:
        """
        Test session setup with CA cert bundle.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        :param tmp_path: Temporary directory path
        :type tmp_path: Path
        """
        ca_cert_file = tmp_path / "ca_cert.pem"
        ca_cert_file.write_text(
            "-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----\n"
        )
        system_certs_file = tmp_path / "system_certs.pem"
        system_certs_file.write_text(
            "-----BEGIN CERTIFICATE-----\nSYSTEM_CERT\n-----END CERTIFICATE-----\n"
        )

        # Create the temp directory that will be returned by mkdtemp mock
        temp_certs_dir = tmp_path / "temp_certs"
        temp_certs_dir.mkdir()

        with (
            patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class,
            patch("src.jamf_pro_sdk.clients.certifi.where") as mock_certifi,
            patch("src.jamf_pro_sdk.clients.tempfile.mkdtemp") as mock_mkdtemp,
        ):
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance
            mock_certifi.return_value = str(system_certs_file)
            mock_mkdtemp.return_value = str(temp_certs_dir)

            session_config = SessionConfig(ca_cert_bundle=str(ca_cert_file))
            client = JamfProClient(
                server="test.jamfcloud.com",
                credentials=mock_credentials,
                session_config=session_config,
            )

            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["verify"] is not False


class TestJamfProClientConcurrentOperations:
    """Test JamfProClient concurrent operations."""

    def test_concurrent_api_requests_success(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """
        Test successful concurrent API requests.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        with patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": 1}
            mock_response.raise_for_status = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = JamfProClient(server="test.jamfcloud.com", credentials=mock_credentials)

            def mock_handler(arg: int) -> httpx.Response:
                return mock_response

            results = list(client.concurrent_api_requests(mock_handler, [1, 2, 3]))
            assert len(results) == 3

    def test_concurrent_api_requests_with_exceptions(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """
        Test concurrent API requests with exception handling.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        with patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            session_config = SessionConfig(return_exceptions=True)
            client = JamfProClient(
                server="test.jamfcloud.com",
                credentials=mock_credentials,
                session_config=session_config,
            )

            def mock_handler(arg: int) -> None:
                if arg == 2:
                    raise ValueError("Test error")
                return arg

            results = list(client.concurrent_api_requests(mock_handler, [1, 2, 3]))
            assert len(results) == 3
            assert isinstance(results[1], ValueError)

    def test_concurrent_api_requests_with_dict_args(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """
        Test concurrent API requests with dictionary arguments.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        with patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            client = JamfProClient(server="test.jamfcloud.com", credentials=mock_credentials)

            def mock_handler(**kwargs: int) -> int:
                return kwargs.get("value", 0)

            args = [{"value": 1}, {"value": 2}, {"value": 3}]
            results = list(client.concurrent_api_requests(mock_handler, args))
            assert len(results) == 3
            assert results == [1, 2, 3]

    def test_concurrent_api_requests_max_concurrency_override(
        self, mock_credentials: UserCredentialsProvider, mocker: "MockerFixture"
    ) -> None:
        """
        Test concurrent API requests with max_concurrency override.

        :param mock_credentials: Mock credentials provider
        :type mock_credentials: UserCredentialsProvider
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        with (
            patch("src.jamf_pro_sdk.clients.httpx.Client") as mock_client_class,
            patch(
                "src.jamf_pro_sdk.clients.concurrent.futures.ThreadPoolExecutor"
            ) as mock_executor_class,
        ):
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            # Create mock executor and context manager
            mock_executor = MagicMock()
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_executor
            mock_context_manager.__exit__.return_value = None
            mock_executor_class.return_value = mock_context_manager

            # Create real Future objects that are already completed
            # This ensures concurrent.futures.wait() works correctly
            def create_completed_future(result_value: int) -> concurrent.futures.Future:
                """Create a completed future with the given result."""
                future = concurrent.futures.Future()
                future.set_result(result_value)
                return future

            # Make submit return different completed futures for each call
            mock_executor.submit.side_effect = [
                create_completed_future(1),
                create_completed_future(2),
                create_completed_future(3),
            ]

            client = JamfProClient(server="test.jamfcloud.com", credentials=mock_credentials)

            def mock_handler(arg: int) -> int:
                return arg

            results = list(
                client.concurrent_api_requests(mock_handler, [1, 2, 3], max_concurrency=2)
            )
            mock_executor_class.assert_called_with(max_workers=2)
            assert results == [1, 2, 3]

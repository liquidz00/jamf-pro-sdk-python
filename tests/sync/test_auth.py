"""Tests for synchronous authentication providers."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest
from src.jamf_pro_sdk.clients.auth import (
    ApiClientCredentialsProvider,
    CredentialsProvider,
    UserCredentialsProvider,
)
from src.jamf_pro_sdk.exceptions import CredentialsError
from src.jamf_pro_sdk.models.client import AccessToken

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_client(mocker: "MockerFixture") -> MagicMock:
    """
    Create a mock JamfProClient.

    :param mocker: Pytest mocker fixture
    :type mocker: MockerFixture
    :return: Mock client
    :rtype: MagicMock
    """
    mock = MagicMock()
    mock.base_server_url = "https://test.jamfcloud.com"
    mock.session = MagicMock()
    return mock


class TestCredentialsProvider:
    """Test base CredentialsProvider class."""

    def test_credentials_provider_initialization(self) -> None:
        """Test CredentialsProvider initialization."""
        provider = CredentialsProvider()
        assert provider._client is None
        assert provider._async_client is None
        assert provider._access_token is not None

    def test_attach_client(self, mock_client: MagicMock) -> None:
        """
        Test attaching a client to credentials provider.

        :param mock_client: Mock client
        :type mock_client: MagicMock
        """
        provider = CredentialsProvider()
        provider.attach_client(mock_client)
        assert provider._client == mock_client

    def test_get_access_token_without_client(self) -> None:
        """Test getting access token without attached client."""
        provider = CredentialsProvider()
        with pytest.raises(CredentialsError, match="A Jamf Pro client is not attached"):
            provider.get_access_token()


class TestUserCredentialsProvider:
    """Test UserCredentialsProvider."""

    def test_user_credentials_provider_initialization(self) -> None:
        """Test UserCredentialsProvider initialization."""
        provider = UserCredentialsProvider(username="test_user", password="test_pass")
        assert provider.username == "test_user"
        assert provider.password == "test_pass"

    def test_request_access_token_success(
        self, mock_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """
        Test successful access token request.

        :param mock_client: Mock client
        :type mock_client: MagicMock
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        provider = UserCredentialsProvider(username="test_user", password="test_pass")
        provider.attach_client(mock_client)

        expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "test_token_123",
            "expires": expires.isoformat(),
        }
        mock_response.raise_for_status = Mock()
        mock_client.session.post.return_value = mock_response

        token = provider._request_access_token()
        assert token.token == "test_token_123"
        assert token.type == "user"

    def test_request_access_token_http_error(
        self, mock_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """
        Test access token request with HTTP error.

        :param mock_client: Mock client
        :type mock_client: MagicMock
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        provider = UserCredentialsProvider(username="test_user", password="test_pass")
        provider.attach_client(mock_client)

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        mock_client.session.post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            provider._request_access_token()

    def test_refresh_access_token_new_token(
        self, mock_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """
        Test token refresh when new token is needed.

        :param mock_client: Mock client
        :type mock_client: MagicMock
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        provider = UserCredentialsProvider(username="test_user", password="test_pass")
        provider.attach_client(mock_client)

        expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "new_token_123",
            "expires": expires.isoformat(),
        }
        mock_response.raise_for_status = Mock()
        mock_client.session.post.return_value = mock_response

        provider._refresh_access_token()
        assert provider._access_token.token == "new_token_123"

    def test_refresh_access_token_cached_token(
        self, mock_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """
        Test token refresh with valid cached token.

        :param mock_client: Mock client
        :type mock_client: MagicMock
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        provider = UserCredentialsProvider(username="test_user", password="test_pass")
        provider.attach_client(mock_client)

        expires = datetime.now(timezone.utc) + timedelta(seconds=120)
        provider._access_token = AccessToken(type="user", token="cached_token", expires=expires)

        provider._refresh_access_token()
        assert provider._access_token.token == "cached_token"
        mock_client.session.post.assert_not_called()

    def test_refresh_access_token_keep_alive(
        self, mock_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """
        Test token refresh using keep-alive endpoint.

        :param mock_client: Mock client
        :type mock_client: MagicMock
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        provider = UserCredentialsProvider(username="test_user", password="test_pass")
        provider.attach_client(mock_client)

        expires = datetime.now(timezone.utc) + timedelta(seconds=30)
        provider._access_token = AccessToken(type="user", token="existing_token", expires=expires)

        new_expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "refreshed_token",
            "expires": new_expires.isoformat(),
        }
        mock_response.raise_for_status = Mock()
        mock_client.session.post.return_value = mock_response

        provider._refresh_access_token()
        assert provider._access_token.token == "refreshed_token"


class TestApiClientCredentialsProvider:
    """Test ApiClientCredentialsProvider."""

    def test_api_client_credentials_provider_initialization(self) -> None:
        """Test ApiClientCredentialsProvider initialization."""
        provider = ApiClientCredentialsProvider(
            client_id="test_client_id", client_secret="test_secret"
        )
        assert provider.client_id == "test_client_id"
        assert provider.client_secret == "test_secret"

    def test_request_access_token_success(
        self, mock_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """
        Test successful OAuth token request.

        :param mock_client: Mock client
        :type mock_client: MagicMock
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        provider = ApiClientCredentialsProvider(
            client_id="test_client_id", client_secret="test_secret"
        )
        provider.attach_client(mock_client)

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "oauth_token_123",
            "expires_in": 3600,
            "scope": "read write",
        }
        mock_response.raise_for_status = Mock()
        mock_client.session.post.return_value = mock_response

        token = provider._request_access_token()
        assert token.token == "oauth_token_123"
        assert token.type == "oauth"
        assert token.scope == ["read", "write"]

    def test_refresh_access_token_oauth_cached(
        self, mock_client: MagicMock, mocker: "MockerFixture"
    ) -> None:
        """
        Test OAuth token refresh with cached token.

        :param mock_client: Mock client
        :type mock_client: MagicMock
        :param mocker: Pytest mocker fixture
        :type mocker: MockerFixture
        """
        provider = ApiClientCredentialsProvider(
            client_id="test_client_id", client_secret="test_secret"
        )
        provider.attach_client(mock_client)

        expires = datetime.now(timezone.utc) + timedelta(seconds=10)
        provider._access_token = AccessToken(
            type="oauth", token="cached_oauth_token", expires=expires
        )

        provider._refresh_access_token()
        assert provider._access_token.token == "cached_oauth_token"
        mock_client.session.post.assert_not_called()


class TestCredentialLoaders:
    """Test credential loader functions."""

    def test_load_from_aws_secrets_manager_user_provider(self, mocker: "MockerFixture") -> None:
        """Test loading UserCredentialsProvider from AWS Secrets Manager."""
        mock_boto3 = mocker.patch("src.jamf_pro_sdk.clients.auth.boto3")
        mock_secrets_client = MagicMock()
        mock_boto3.client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.return_value = {
            "SecretString": '{"username": "test_user", "password": "test_pass"}'
        }

        from src.jamf_pro_sdk.clients.auth import (
            UserCredentialsProvider,
            load_from_aws_secrets_manager,
        )

        provider = load_from_aws_secrets_manager(UserCredentialsProvider, secret_id="test-secret")
        assert isinstance(provider, UserCredentialsProvider)
        assert provider.username == "test_user"
        assert provider.password == "test_pass"

    def test_load_from_aws_secrets_manager_api_client_provider(
        self, mocker: "MockerFixture"
    ) -> None:
        """Test loading ApiClientCredentialsProvider from AWS Secrets Manager."""
        mock_boto3 = mocker.patch("src.jamf_pro_sdk.clients.auth.boto3")
        mock_secrets_client = MagicMock()
        mock_boto3.client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.return_value = {
            "SecretString": '{"client_id": "test_id", "client_secret": "test_secret"}'
        }

        from src.jamf_pro_sdk.clients.auth import (
            ApiClientCredentialsProvider,
            load_from_aws_secrets_manager,
        )

        provider = load_from_aws_secrets_manager(
            ApiClientCredentialsProvider, secret_id="test-secret"
        )
        assert isinstance(provider, ApiClientCredentialsProvider)
        assert provider.client_id == "test_id"
        assert provider.client_secret == "test_secret"

    def test_load_from_aws_secrets_manager_missing_dependency(
        self, mocker: "MockerFixture"
    ) -> None:
        """Test AWS Secrets Manager loader without boto3."""
        mocker.patch("src.jamf_pro_sdk.clients.auth.BOTO3_IS_INSTALLED", False)

        from src.jamf_pro_sdk.clients.auth import (
            UserCredentialsProvider,
            load_from_aws_secrets_manager,
        )

        with pytest.raises(ImportError, match="aws.*extra dependency"):
            load_from_aws_secrets_manager(UserCredentialsProvider, secret_id="test")

    def test_load_from_keychain_user_provider(self, mocker: "MockerFixture") -> None:
        """Test loading UserCredentialsProvider from keychain."""
        mock_keyring = mocker.patch("src.jamf_pro_sdk.clients.auth.keyring")
        mock_keyring.get_password.return_value = "test_password"

        from src.jamf_pro_sdk.clients.auth import (
            UserCredentialsProvider,
            load_from_keychain,
        )

        provider = load_from_keychain(
            UserCredentialsProvider, server="test.jamfcloud.com", username="test_user"
        )
        assert isinstance(provider, UserCredentialsProvider)
        assert provider.username == "test_user"
        assert provider.password == "test_password"

    def test_load_from_keychain_api_client_provider(self, mocker: "MockerFixture") -> None:
        """Test loading ApiClientCredentialsProvider from keychain."""
        mock_keyring = mocker.patch("src.jamf_pro_sdk.clients.auth.keyring")
        mock_keyring.get_password.return_value = "test_secret"

        from src.jamf_pro_sdk.clients.auth import (
            ApiClientCredentialsProvider,
            load_from_keychain,
        )

        provider = load_from_keychain(
            ApiClientCredentialsProvider,
            server="test.jamfcloud.com",
            client_id="test_client_id",
        )
        assert isinstance(provider, ApiClientCredentialsProvider)
        assert provider.client_id == "test_client_id"
        assert provider.client_secret == "test_secret"

    def test_load_from_keychain_missing_dependency(self, mocker: "MockerFixture") -> None:
        """Test keychain loader without keyring."""
        mocker.patch("src.jamf_pro_sdk.clients.auth.KEYRING_IS_INSTALLED", False)

        from src.jamf_pro_sdk.clients.auth import (
            UserCredentialsProvider,
            load_from_keychain,
        )

        with pytest.raises(ImportError, match="macOS.*extra dependency"):
            load_from_keychain(
                UserCredentialsProvider, server="test.jamfcloud.com", username="test"
            )

    def test_load_from_keychain_password_not_found(self, mocker: "MockerFixture") -> None:
        """Test keychain loader when password is not found."""
        mock_keyring = mocker.patch("src.jamf_pro_sdk.clients.auth.keyring")
        mock_keyring.get_password.return_value = None

        from src.jamf_pro_sdk.clients.auth import (
            UserCredentialsProvider,
            load_from_keychain,
        )

        with pytest.raises(CredentialsError, match="Password not found"):
            load_from_keychain(
                UserCredentialsProvider, server="test.jamfcloud.com", username="test"
            )

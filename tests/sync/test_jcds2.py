"""Tests for JCDS2 synchronous functionality."""

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import httpx
import pytest
from src.jamf_pro_sdk.clients.jcds2 import (
    JCDS2,
    FileUpload,
    JCDS2FileExistsError,
    JCDS2FileNotFoundError,
)
from src.jamf_pro_sdk.models.classic.packages import ClassicPackage, ClassicPackageItem
from src.jamf_pro_sdk.models.pro.jcds2 import DownloadUrl, File, NewFile

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_classic_api(mocker: "MockerFixture") -> MagicMock:
    """Create a mock Classic API client."""
    return MagicMock()


@pytest.fixture
def mock_pro_api(mocker: "MockerFixture") -> MagicMock:
    """Create a mock Pro API client."""
    return MagicMock()


@pytest.fixture
def mock_concurrent_method(mocker: "MockerFixture") -> MagicMock:
    """Create a mock concurrent requests method."""
    return MagicMock()


@pytest.fixture
def jcds2_client(
    mock_classic_api: MagicMock,
    mock_pro_api: MagicMock,
    mock_concurrent_method: MagicMock,
) -> JCDS2:
    """Create a JCDS2 client instance with mocked dependencies."""
    return JCDS2(
        classic_api_client=mock_classic_api,
        pro_api_client=mock_pro_api,
        concurrent_requests_method=mock_concurrent_method,
    )


@pytest.fixture
def sample_file() -> Path:
    """Create a temporary file for testing."""
    with NamedTemporaryFile(delete=False, suffix=".pkg") as tmp_file:
        tmp_file.write(b"test file content" * 100)  # Small file for testing
        tmp_path = Path(tmp_file.name)
    yield tmp_path
    tmp_path.unlink(missing_ok=True)


@pytest.fixture
def mock_new_jcds_file() -> NewFile:
    """Create a mock NewFile response."""
    from datetime import datetime, timedelta, timezone

    return NewFile(
        accessKeyID="test_access_key",
        secretAccessKey="test_secret_key",
        sessionToken="test_session_token",
        region="us-east-1",
        expiration=datetime.now(timezone.utc) + timedelta(hours=1),
        bucketName="test-bucket",
        path="test/path/",
        uuid=uuid4(),
    )


@pytest.fixture
def mock_download_file() -> File:
    """Create a mock File response."""
    return File(
        region="us-east-1",
        fileName="test.pkg",
        length=1700,  # Matches sample_file size
        md5="test_md5",
        sha3="test_sha3",
    )


@pytest.fixture
def mock_download_url() -> DownloadUrl:
    """Create a mock DownloadUrl response."""
    return DownloadUrl(uri="https://test-bucket.s3.amazonaws.com/test.pkg")


class TestFileUpload:
    """Test FileUpload class."""

    def test_file_upload_initialization(self, sample_file: Path) -> None:
        """Test FileUpload initialization."""
        file_upload = FileUpload(sample_file)
        assert file_upload.path == sample_file
        assert file_upload.size > 0
        assert file_upload.total_chunks >= 1

    def test_file_upload_get_chunk(self, sample_file: Path) -> None:
        """Test getting a chunk from FileUpload."""
        file_upload = FileUpload(sample_file)
        chunk = file_upload.get_chunk(0)
        assert isinstance(chunk, bytes)
        assert len(chunk) > 0

    def test_file_upload_get_chunk_invalid(self, sample_file: Path) -> None:
        """Test getting an invalid chunk number."""
        file_upload = FileUpload(sample_file)
        with pytest.raises(ValueError, match="Chunk number must be less than"):
            file_upload.get_chunk(file_upload.total_chunks + 1)


class TestJCDS2Upload:
    """Test JCDS2 upload operations."""

    @patch("src.jamf_pro_sdk.clients.jcds2.boto3")
    def test_upload_file_single_upload(
        self,
        mock_boto3: MagicMock,
        jcds2_client: JCDS2,
        sample_file: Path,
        mock_new_jcds_file: NewFile,
        mock_classic_api: MagicMock,
        mock_pro_api: MagicMock,
    ) -> None:
        """Test single file upload (file < 1 GiB)."""
        # Setup mocks
        mock_classic_api.list_all_packages.return_value = []
        mock_pro_api.create_jcds_file_v1.return_value = mock_new_jcds_file
        mock_classic_api.create_package.return_value = 123

        mock_s3_client = MagicMock()
        mock_s3_client.put_object.return_value = {"ETag": "test-etag"}
        mock_session = MagicMock()
        mock_session.client.return_value = mock_s3_client
        mock_boto3.Session.return_value = mock_session

        # Execute
        jcds2_client.upload_file(sample_file)

        # Verify
        mock_pro_api.create_jcds_file_v1.assert_called_once()
        mock_s3_client.put_object.assert_called_once()
        mock_classic_api.create_package.assert_called_once()

    @patch("src.jamf_pro_sdk.clients.jcds2.boto3")
    def test_upload_file_multipart_upload(
        self,
        mock_boto3: MagicMock,
        jcds2_client: JCDS2,
        mock_new_jcds_file: NewFile,
        mock_classic_api: MagicMock,
        mock_pro_api: MagicMock,
        mock_concurrent_method: MagicMock,
    ) -> None:
        """Test multipart file upload (file >= 1 GiB)."""
        # Create a large file (simulated by mocking FileUpload)
        with NamedTemporaryFile(delete=False, suffix=".pkg") as tmp_file:
            # Write enough data to trigger multipart (1 GiB = 1073741824 bytes)
            tmp_file.write(b"x" * 1073741824)
            large_file = Path(tmp_file.name)

        try:
            # Setup mocks
            mock_classic_api.list_all_packages.return_value = []
            mock_pro_api.create_jcds_file_v1.return_value = mock_new_jcds_file

            mock_multipart_upload = {
                "Bucket": "test-bucket",
                "Key": "test/path/test.pkg",
                "UploadId": "test-upload-id",
            }
            mock_s3_client = MagicMock()
            mock_s3_client.create_multipart_upload.return_value = mock_multipart_upload
            mock_s3_client.complete_multipart_upload.return_value = {"ETag": "test-etag"}
            mock_session = MagicMock()
            mock_session.client.return_value = mock_s3_client
            mock_boto3.Session.return_value = mock_session

            # Mock concurrent method to return upload parts
            mock_concurrent_method.return_value = iter(
                [{"PartNumber": 1, "ETag": "etag1"}, {"PartNumber": 2, "ETag": "etag2"}]
            )
            mock_classic_api.create_package.return_value = 123

            # Execute
            jcds2_client.upload_file(large_file)

            # Verify
            mock_s3_client.create_multipart_upload.assert_called_once()
            mock_s3_client.complete_multipart_upload.assert_called_once()
            mock_classic_api.create_package.assert_called_once()
        finally:
            large_file.unlink(missing_ok=True)

    def test_upload_file_file_not_found(self, jcds2_client: JCDS2) -> None:
        """Test upload_file raises FileNotFoundError for non-existent file."""
        non_existent_file = Path("/nonexistent/file.pkg")
        with pytest.raises(FileNotFoundError):
            jcds2_client.upload_file(non_existent_file)

    def test_upload_file_file_exists_error(
        self,
        jcds2_client: JCDS2,
        sample_file: Path,
        mock_classic_api: MagicMock,
    ) -> None:
        """Test upload_file raises JCDS2FileExistsError when file exists."""
        existing_package = ClassicPackageItem(id=1, name="Existing Package")
        existing_package.filename = sample_file.name
        mock_classic_api.list_all_packages.return_value = [1]
        mock_classic_api.get_package_by_id.return_value = existing_package

        with pytest.raises(JCDS2FileExistsError):
            jcds2_client.upload_file(sample_file)

    @patch("src.jamf_pro_sdk.clients.jcds2.boto3", None)
    def test_upload_file_boto3_not_installed(self, jcds2_client: JCDS2, sample_file: Path) -> None:
        """Test upload_file raises ImportError when boto3 is not installed."""
        with patch("src.jamf_pro_sdk.clients.jcds2.BOTO3_IS_INSTALLED", False):
            with pytest.raises(ImportError, match="aws.*extra dependency"):
                jcds2_client.upload_file(sample_file)


class TestJCDS2Download:
    """Test JCDS2 download operations."""

    def test_download_file_success(
        self,
        jcds2_client: JCDS2,
        mock_pro_api: MagicMock,
        mock_concurrent_method: MagicMock,
        mock_download_file: File,
        mock_download_url: DownloadUrl,
    ) -> None:
        """Test successful file download."""
        with TemporaryDirectory() as tmp_dir:
            download_path = Path(tmp_dir) / "downloaded.pkg"

            # Setup mocks
            mock_pro_api.get_jcds_file_v1.return_value = mock_download_url

            # Mock httpx.Client
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.headers = {"Content-Length": "1700"}
            mock_response.raise_for_status = Mock()

            mock_client = MagicMock()
            mock_client.head.return_value = mock_response
            mock_client.get.return_value = mock_response
            mock_response.content = b"test content"

            with patch("src.jamf_pro_sdk.clients.jcds2.httpx.Client", return_value=mock_client):
                # Mock concurrent method to simulate chunk downloads
                mock_concurrent_method.return_value = iter([None, None])

                # Execute
                jcds2_client.download_file("test.pkg", download_path)

                # Verify
                mock_pro_api.get_jcds_file_v1.assert_called_once_with(file_name="test.pkg")
                assert download_path.exists()

    def test_download_file_not_found(
        self,
        jcds2_client: JCDS2,
        mock_pro_api: MagicMock,
    ) -> None:
        """Test download_file raises JCDS2FileNotFoundError for non-existent file."""
        error_response = MagicMock()
        error_response.status_code = 404
        http_error = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=error_response
        )
        mock_pro_api.get_jcds_file_v1.side_effect = http_error

        with pytest.raises(JCDS2FileNotFoundError):
            jcds2_client.download_file("nonexistent.pkg", "/tmp/test.pkg")

    def test_download_file_to_directory(
        self,
        jcds2_client: JCDS2,
        mock_pro_api: MagicMock,
        mock_download_url: DownloadUrl,
    ) -> None:
        """Test download_file appends filename when download_path is a directory."""
        with TemporaryDirectory() as tmp_dir:
            download_dir = Path(tmp_dir)

            # Setup mocks
            mock_pro_api.get_jcds_file_v1.return_value = mock_download_url

            mock_response = MagicMock(spec=httpx.Response)
            mock_response.headers = {"Content-Length": "1700"}
            mock_response.raise_for_status = Mock()

            mock_client = MagicMock()
            mock_client.head.return_value = mock_response
            mock_client.get.return_value = mock_response
            mock_response.content = b"test content"

            with patch("src.jamf_pro_sdk.clients.jcds2.httpx.Client", return_value=mock_client):
                with patch.object(
                    jcds2_client, "concurrent_api_requests", return_value=iter([None])
                ):
                    # Execute
                    jcds2_client.download_file("test.pkg", download_dir)

                    # Verify file was created in directory with correct name
                    expected_file = download_dir / "test.pkg"
                    assert expected_file.exists()

    def test_download_file_path_exists(
        self,
        jcds2_client: JCDS2,
        sample_file: Path,
    ) -> None:
        """Test download_file raises FileExistsError when path exists."""
        with pytest.raises(FileExistsError, match="already exists"):
            jcds2_client.download_file("test.pkg", sample_file)

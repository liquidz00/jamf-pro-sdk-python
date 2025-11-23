"""Tests for JCDS2 asynchronous functionality."""

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import httpx
import pytest
from src.jamf_pro_sdk.clients.jcds2 import (
    AsyncJCDS2,
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
def mock_async_classic_api(mocker: "MockerFixture") -> MagicMock:
    """Create a mock Async Classic API client."""
    return MagicMock()


@pytest.fixture
def mock_async_pro_api(mocker: "MockerFixture") -> MagicMock:
    """Create a mock Async Pro API client."""
    return MagicMock()


@pytest.fixture
def mock_async_concurrent_method(mocker: "MockerFixture") -> MagicMock:
    """Create a mock async concurrent requests method."""
    return MagicMock()


@pytest.fixture
def async_jcds2_client(
    mock_async_classic_api: MagicMock,
    mock_async_pro_api: MagicMock,
    mock_async_concurrent_method: MagicMock,
) -> AsyncJCDS2:
    """Create an AsyncJCDS2 client instance with mocked dependencies."""
    return AsyncJCDS2(
        classic_api_client=mock_async_classic_api,
        pro_api_client=mock_async_pro_api,
        concurrent_requests_method=mock_async_concurrent_method,
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


@pytest.mark.asyncio
class TestAsyncJCDS2Upload:
    """Test AsyncJCDS2 upload operations."""

    @patch("src.jamf_pro_sdk.clients.jcds2.boto3")
    async def test_upload_file_single_upload(
        self,
        mock_boto3: MagicMock,
        async_jcds2_client: AsyncJCDS2,
        sample_file: Path,
        mock_new_jcds_file: NewFile,
        mock_async_classic_api: MagicMock,
        mock_async_pro_api: MagicMock,
    ) -> None:
        """Test single file upload (file < 1 GiB)."""
        # Setup mocks
        mock_async_classic_api.list_all_packages = AsyncMock(return_value=[])
        mock_async_pro_api.create_jcds_file_v1 = AsyncMock(return_value=mock_new_jcds_file)
        mock_async_classic_api.create_package = AsyncMock(return_value=123)

        mock_s3_client = MagicMock()
        mock_s3_client.put_object.return_value = {"ETag": "test-etag"}
        mock_session = MagicMock()
        mock_session.client.return_value = mock_s3_client
        mock_boto3.Session.return_value = mock_session

        # Mock asyncio.get_event_loop().run_in_executor
        with patch("asyncio.get_event_loop") as mock_loop:
            call_count = 0

            async def mock_executor(*args, **kwargs):
                """Mock executor that returns session for first call, put_object result for second."""
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    # First call is boto3.Session()
                    return mock_session
                else:
                    # Second call is s3_client.put_object()
                    return {"ETag": "test-etag"}

            mock_loop.return_value.run_in_executor = AsyncMock(side_effect=mock_executor)

            # Execute
            await async_jcds2_client.upload_file(sample_file)

            # Verify
            mock_async_pro_api.create_jcds_file_v1.assert_called_once()
            mock_async_classic_api.create_package.assert_called_once()

    @patch("src.jamf_pro_sdk.clients.jcds2.boto3")
    async def test_upload_file_multipart_upload(
        self,
        mock_boto3: MagicMock,
        async_jcds2_client: AsyncJCDS2,
        mock_new_jcds_file: NewFile,
        mock_async_classic_api: MagicMock,
        mock_async_pro_api: MagicMock,
        mock_async_concurrent_method: MagicMock,
    ) -> None:
        """Test multipart file upload (file >= 1 GiB)."""
        # Create a large file (simulated by mocking FileUpload)
        with NamedTemporaryFile(delete=False, suffix=".pkg") as tmp_file:
            # Write enough data to trigger multipart (1 GiB = 1073741824 bytes)
            tmp_file.write(b"x" * 1073741824)
            large_file = Path(tmp_file.name)

        try:
            # Setup mocks
            mock_async_classic_api.list_all_packages = AsyncMock(return_value=[])
            mock_async_pro_api.create_jcds_file_v1 = AsyncMock(return_value=mock_new_jcds_file)

            mock_multipart_upload = {
                "Bucket": "test-bucket",
                "Key": "test/path/test.pkg",
                "UploadId": "test-upload-id",
            }
            mock_s3_client = MagicMock()
            mock_s3_client.create_multipart_upload.return_value = mock_multipart_upload
            mock_s3_client.complete_multipart_upload.return_value = {"ETag": "test-etag"}
            mock_s3_client.upload_part.return_value = {"ETag": "etag1"}
            mock_session = MagicMock()
            mock_session.client.return_value = mock_s3_client
            mock_boto3.Session.return_value = mock_session

            # Mock concurrent method to return upload parts
            async def async_part_generator():
                """Async generator for upload parts."""
                yield {"PartNumber": 1, "ETag": "etag1"}
                yield {"PartNumber": 2, "ETag": "etag2"}

            mock_async_concurrent_method.return_value = async_part_generator()
            mock_async_classic_api.create_package = AsyncMock(return_value=123)

            # Mock asyncio.get_event_loop().run_in_executor
            with patch("asyncio.get_event_loop") as mock_loop:
                call_count = 0

                async def mock_executor(*args, **kwargs):
                    """Mock executor that returns different values based on call count."""
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        return mock_session  # boto3.Session()
                    elif call_count == 2:
                        return mock_multipart_upload  # create_multipart_upload
                    elif call_count <= 4:
                        return {"ETag": f"etag{call_count - 2}"}  # upload_part calls
                    else:
                        return {"ETag": "test-etag"}  # complete_multipart_upload

                mock_loop.return_value.run_in_executor = AsyncMock(side_effect=mock_executor)

                # Execute
                await async_jcds2_client.upload_file(large_file)

                # Verify
                mock_async_pro_api.create_jcds_file_v1.assert_called_once()
                mock_async_classic_api.create_package.assert_called_once()
        finally:
            large_file.unlink(missing_ok=True)

    async def test_upload_file_file_not_found(self, async_jcds2_client: AsyncJCDS2) -> None:
        """Test upload_file raises FileNotFoundError for non-existent file."""
        non_existent_file = Path("/nonexistent/file.pkg")
        with pytest.raises(FileNotFoundError):
            await async_jcds2_client.upload_file(non_existent_file)

    async def test_upload_file_file_exists_error(
        self,
        async_jcds2_client: AsyncJCDS2,
        sample_file: Path,
        mock_async_classic_api: MagicMock,
    ) -> None:
        """Test upload_file raises JCDS2FileExistsError when file exists."""
        existing_package = ClassicPackageItem(id=1, name="Existing Package")
        existing_package.filename = sample_file.name
        mock_async_classic_api.list_all_packages = AsyncMock(return_value=[1])
        mock_async_classic_api.get_package_by_id = AsyncMock(return_value=existing_package)

        with pytest.raises(JCDS2FileExistsError):
            await async_jcds2_client.upload_file(sample_file)

    @patch("src.jamf_pro_sdk.clients.jcds2.boto3", None)
    async def test_upload_file_boto3_not_installed(
        self, async_jcds2_client: AsyncJCDS2, sample_file: Path
    ) -> None:
        """Test upload_file raises ImportError when boto3 is not installed."""
        with patch("src.jamf_pro_sdk.clients.jcds2.BOTO3_IS_INSTALLED", False):
            with pytest.raises(ImportError, match="aws.*extra dependency"):
                await async_jcds2_client.upload_file(sample_file)


@pytest.mark.asyncio
class TestAsyncJCDS2Download:
    """Test AsyncJCDS2 download operations."""

    async def test_download_file_success(
        self,
        async_jcds2_client: AsyncJCDS2,
        mock_async_pro_api: MagicMock,
        mock_async_concurrent_method: MagicMock,
        mock_download_url: DownloadUrl,
    ) -> None:
        """Test successful file download."""
        with TemporaryDirectory() as tmp_dir:
            download_path = Path(tmp_dir) / "downloaded.pkg"

            # Setup mocks
            mock_async_pro_api.get_jcds_file_v1 = AsyncMock(return_value=mock_download_url)

            # Mock httpx.AsyncClient
            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.headers = {"Content-Length": "1700"}
            mock_response.raise_for_status = Mock()  # raise_for_status is synchronous
            mock_response.content = b"test content"

            mock_async_client = AsyncMock(spec=httpx.AsyncClient)
            mock_async_client.head = AsyncMock(return_value=mock_response)
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=None)
            mock_async_client.aclose = AsyncMock()

            # Mock concurrent method to simulate chunk downloads
            async def async_chunk_generator():
                """Async generator for chunk downloads."""
                yield None
                yield None

            mock_async_concurrent_method.return_value = async_chunk_generator()

            with patch(
                "src.jamf_pro_sdk.clients.jcds2.httpx.AsyncClient", return_value=mock_async_client
            ):
                # Execute
                await async_jcds2_client.download_file("test.pkg", download_path)

                # Verify
                mock_async_pro_api.get_jcds_file_v1.assert_called_once_with(file_name="test.pkg")
                mock_async_client.aclose.assert_called_once()

    async def test_download_file_not_found(
        self,
        async_jcds2_client: AsyncJCDS2,
        mock_async_pro_api: MagicMock,
    ) -> None:
        """Test download_file raises JCDS2FileNotFoundError for non-existent file."""
        error_response = MagicMock()
        error_response.status_code = 404
        http_error = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=error_response
        )
        mock_async_pro_api.get_jcds_file_v1 = AsyncMock(side_effect=http_error)

        with pytest.raises(JCDS2FileNotFoundError):
            await async_jcds2_client.download_file("nonexistent.pkg", "/tmp/test.pkg")

    async def test_download_file_to_directory(
        self,
        async_jcds2_client: AsyncJCDS2,
        mock_async_pro_api: MagicMock,
        mock_download_url: DownloadUrl,
        mock_async_concurrent_method: MagicMock,
    ) -> None:
        """Test download_file appends filename when download_path is a directory."""
        with TemporaryDirectory() as tmp_dir:
            download_dir = Path(tmp_dir)

            # Setup mocks
            mock_async_pro_api.get_jcds_file_v1 = AsyncMock(return_value=mock_download_url)

            mock_response = AsyncMock(spec=httpx.Response)
            mock_response.headers = {"Content-Length": "1700"}
            mock_response.raise_for_status = Mock()  # raise_for_status is synchronous
            mock_response.content = b"test content"

            mock_async_client = AsyncMock(spec=httpx.AsyncClient)
            mock_async_client.head = AsyncMock(return_value=mock_response)
            mock_async_client.get = AsyncMock(return_value=mock_response)
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=None)
            mock_async_client.aclose = AsyncMock()

            # Mock concurrent method
            async def async_chunk_generator():
                """Async generator for chunk downloads."""
                yield None

            mock_async_concurrent_method.return_value = async_chunk_generator()

            with patch(
                "src.jamf_pro_sdk.clients.jcds2.httpx.AsyncClient", return_value=mock_async_client
            ):
                # Execute
                await async_jcds2_client.download_file("test.pkg", download_dir)

                # Verify file was created in directory with correct name
                expected_file = download_dir / "test.pkg"
                assert expected_file.exists()

    async def test_download_file_path_exists(
        self,
        async_jcds2_client: AsyncJCDS2,
        sample_file: Path,
    ) -> None:
        """Test download_file raises FileExistsError when path exists."""
        with pytest.raises(FileExistsError, match="already exists"):
            await async_jcds2_client.download_file("test.pkg", sample_file)

from __future__ import annotations

import asyncio
import logging
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, AsyncIterator, Callable, Iterator

import httpx

try:
    import boto3
except ImportError:
    BOTO3_IS_INSTALLED = False
    boto3 = None
else:
    BOTO3_IS_INSTALLED = True

from ..models.classic.packages import ClassicPackage
from ..models.pro.jcds2 import NewFile

if TYPE_CHECKING:
    from .classic_api import AsyncClassicApi, ClassicApi
    from .pro_api import AsyncProApi, ProApi

CHUNK_SIZE = 1024 * 1024 * 20  # 20 MB

logger = logging.getLogger("jamf_pro_sdk")


class JCDS2FileExistsError(Exception):
    """The file already exists in Jamf Pro associated to a package."""


class JCDS2FileNotFoundError(Exception):
    """The requested file does not exist in the JCDS."""


class FileUpload:
    """Represents a file that will be uploaded to the JCDS."""

    def __init__(self, path: Path):
        self.path = path
        self.size = path.stat().st_size
        self.total_chunks = math.ceil(self.size / CHUNK_SIZE)

    def get_chunk(self, chunk_number: int) -> bytes:
        """Returns a range of bytes for a given chunk (index)."""
        if chunk_number > self.total_chunks:
            raise ValueError(f"Chunk number must be less than or equal to {self.total_chunks}")

        with open(self.path, "rb") as fobj:
            fobj.seek(chunk_number * CHUNK_SIZE)
            return fobj.read(CHUNK_SIZE)


class JCDS2:
    """Provides an interface to manage files in JCDS2."""

    def __init__(
        self,
        classic_api_client: ClassicApi,
        pro_api_client: ProApi,
        concurrent_requests_method: Callable[..., Iterator],
    ):
        self.classic_api_client = classic_api_client
        self.pro_api_client = pro_api_client
        self.concurrent_api_requests = concurrent_requests_method

    @staticmethod
    def _upload_file(s3_client, jcds_file: NewFile, file_upload: FileUpload):
        logger.info("JCDS2-Upload %s ", file_upload.path)
        with open(file_upload.path, "rb") as fobj:
            resp = s3_client.put_object(
                Body=fobj,
                Bucket=jcds_file.bucketName,
                Key=f"{jcds_file.path}{file_upload.path.name}",
            )
            logger.debug(resp)

    def _upload_multipart(self, s3_client, jcds_file: NewFile, file_upload: FileUpload):
        logger.info("JCDS2-UploadMultipart %s", file_upload.path)
        multipart_upload = s3_client.create_multipart_upload(
            Bucket=jcds_file.bucketName, Key=f"{jcds_file.path}{file_upload.path.name}"
        )
        logger.debug(multipart_upload)

        multipart_upload_parts = list()

        for r in self.concurrent_api_requests(
            handler=self._upload_part,
            arguments=[
                {
                    "s3_client": s3_client,
                    "part_number": i,
                    "file_upload": file_upload,
                    "multipart_upload": multipart_upload,
                }
                for i in range(1, file_upload.total_chunks + 1)
            ],
        ):
            multipart_upload_parts.append(r)

        try:
            multipart_upload_complete = s3_client.complete_multipart_upload(
                Bucket=multipart_upload["Bucket"],
                Key=multipart_upload["Key"],
                MultipartUpload={"Parts": multipart_upload_parts},
                UploadId=multipart_upload["UploadId"],
            )
            logger.debug(multipart_upload_complete)
        except:
            logger.error("JCDS2-UploadMultipart-Aborted %s", file_upload.path)
            multipart_aborted = s3_client.abort_multipart_upload(
                Bucket=multipart_upload["Bucket"],
                Key=multipart_upload["Key"],
                UploadId=multipart_upload["UploadId"],
            )
            logger.debug(multipart_aborted)
            raise

    @staticmethod
    def _upload_part(s3_client, multipart_upload: dict, part_number: int, file_upload: FileUpload):
        logger.info("JCDS2-UploadMultipart-Part %s %s", part_number, file_upload.path.name)
        # TODO: Retry functionality if a part upload fails
        part_resp = s3_client.upload_part(
            Body=file_upload.get_chunk(part_number - 1),
            Bucket=multipart_upload["Bucket"],
            Key=multipart_upload["Key"],
            PartNumber=part_number,
            UploadId=multipart_upload["UploadId"],
        )
        logger.debug(part_resp)
        return {"PartNumber": part_number, "ETag": part_resp["ETag"]}

    def upload_file(self, file_path: str | Path) -> None:
        """Upload a file to the JCDS and create the package object.

        If the file is less than 1 GiB in size the upload will be performed in a single request. If
        the file is greater than 1 GiB in size a multipart upload operation will be performed.

        A ``JCDS2FileExistsError`` is raised if any file of the same name exists and is associated to
        a package.

        .. important::

            This operation requires the ``aws`` extra dependency.

        :param file_path: The path to the file to upload. Will raise ``FileNotFoundError`` if the path
            to the file's location does not exist.
        :type file_path: str | Path
        """
        if not BOTO3_IS_INSTALLED:
            raise ImportError("The 'aws' extra dependency is required.")

        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError("A file or directory at the download path already exists")

        file_upload = FileUpload(file_path)

        packages = [
            self.classic_api_client.get_package_by_id(p)
            for p in self.classic_api_client.list_all_packages()
        ]

        for p in packages:
            if file_upload.path.name == p.filename:
                raise JCDS2FileExistsError(
                    f"The file '{file_upload.path.name}' exists and is associated to package ({p.id}) '{p.name}'"
                )

        new_jcds_file = self.pro_api_client.create_jcds_file_v1()

        boto3_session = boto3.Session(
            aws_access_key_id=new_jcds_file.accessKeyID,
            aws_secret_access_key=new_jcds_file.secretAccessKey,
            aws_session_token=new_jcds_file.sessionToken,
            region_name=new_jcds_file.region,
        )

        s3_client = boto3_session.client(service_name="s3")

        try:
            # if file_upload.size < 5368709120:  # 5 GiB
            if file_upload.size < 1073741824:  # 1 GiB
                self._upload_file(
                    s3_client=s3_client, jcds_file=new_jcds_file, file_upload=file_upload
                )
            else:
                self._upload_multipart(
                    s3_client=s3_client, jcds_file=new_jcds_file, file_upload=file_upload
                )
        except Exception as err:
            logger.exception(err)
            raise
        else:
            new_package = ClassicPackage(name=file_path.name, filename=file_path.name)
            new_pkg_resp = self.classic_api_client.create_package(data=new_package)
            logger.debug(new_pkg_resp)

    @staticmethod
    def _download_range(session: httpx.Client, url: str, index: int, temp_dir: str):
        range_start = index * CHUNK_SIZE
        range_end = ((index + 1) * CHUNK_SIZE) - 1
        range_response = session.get(
            url, headers={"Range": f"bytes={range_start}-{range_end}"}, timeout=60
        )
        range_response.raise_for_status()
        logger.debug(range_response.headers)
        with open(temp_dir + f"/chunk_{str(index).zfill(9)}", "wb") as fobj:
            fobj.write(range_response.content)

    def download_file(self, file_name: str, download_path: str | Path) -> None:
        """Download a file from the JCDS by filename.

        :param file_name: The name of the file in the JCDS to download.
        :type file_name: str

        :param download_path: The path to download the file to. If the provided path is directory
            the file name will be appended to it. Will raise `FileExistsError` if the path is to a
            file location that already exists.
        :type download_path: str | Path
        """
        if not isinstance(download_path, Path):
            download_path = Path(download_path)

        if download_path.is_dir():
            download_path = download_path / file_name

        if download_path.exists():
            raise FileExistsError("A file or directory at the download path already exists")

        try:
            download_file = self.pro_api_client.get_jcds_file_v1(file_name=file_name)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                raise JCDS2FileNotFoundError(f"The file '{file_name}' does not exist")
            else:
                raise

        # TODO: Retry feature that's not relying on urllib3's implementation
        limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
        download_session = httpx.Client(limits=limits, timeout=httpx.Timeout(60))

        download_file_head = download_session.head(download_file.uri)
        download_file_head.raise_for_status()
        total_chunks = math.ceil(int(download_file_head.headers["Content-Length"]) / CHUNK_SIZE)

        temp_dir = TemporaryDirectory(prefix="jcds2-download-")
        logger.debug("JCDS2-Download-TempDir %s", temp_dir.name)

        r = self.concurrent_api_requests(
            handler=self._download_range,
            arguments=[
                {
                    "session": download_session,
                    "url": download_file.uri,
                    "index": i,
                    "temp_dir": temp_dir.name,
                }
                for i in range(0, total_chunks)
            ],
            max_concurrency=5,
        )
        list(r)

        with open(download_path, "ab") as fobj:
            for chunk in sorted(Path(temp_dir.name).glob("chunk_*")):
                with open(chunk, "rb") as chunk_fobj:
                    fobj.write(chunk_fobj.read())


class AsyncJCDS2:
    """Provides an async interface to manage files in JCDS2."""

    def __init__(
        self,
        classic_api_client: "AsyncClassicApi",
        pro_api_client: "AsyncProApi",
        concurrent_requests_method: Callable[..., AsyncIterator],
    ):
        self.classic_api_client = classic_api_client
        self.pro_api_client = pro_api_client
        self.concurrent_api_requests = concurrent_requests_method

    @staticmethod
    async def _upload_file(s3_client, jcds_file: NewFile, file_upload: FileUpload):
        """Upload a file to S3."""
        logger.info("JCDS2-Upload %s ", file_upload.path)
        # boto3 operations are blocking, so run in thread
        loop = asyncio.get_event_loop()
        with open(file_upload.path, "rb") as fobj:
            resp = await loop.run_in_executor(
                None,
                lambda: s3_client.put_object(
                    Body=fobj.read(),
                    Bucket=jcds_file.bucketName,
                    Key=f"{jcds_file.path}{file_upload.path.name}",
                ),
            )
            logger.debug(resp)

    async def _upload_multipart(self, s3_client, jcds_file: NewFile, file_upload: FileUpload):
        """Upload a file using multipart upload."""
        logger.info("JCDS2-UploadMultipart %s", file_upload.path)
        loop = asyncio.get_event_loop()

        # Create multipart upload (blocking operation)
        multipart_upload = await loop.run_in_executor(
            None,
            lambda: s3_client.create_multipart_upload(
                Bucket=jcds_file.bucketName, Key=f"{jcds_file.path}{file_upload.path.name}"
            ),
        )
        logger.debug(multipart_upload)

        multipart_upload_parts = list()

        async for r in self.concurrent_api_requests(
            handler=self._upload_part,
            arguments=[
                {
                    "s3_client": s3_client,
                    "part_number": i,
                    "file_upload": file_upload,
                    "multipart_upload": multipart_upload,
                }
                for i in range(1, file_upload.total_chunks + 1)
            ],
        ):
            multipart_upload_parts.append(r)

        try:
            multipart_upload_complete = await loop.run_in_executor(
                None,
                lambda: s3_client.complete_multipart_upload(
                    Bucket=multipart_upload["Bucket"],
                    Key=multipart_upload["Key"],
                    MultipartUpload={"Parts": multipart_upload_parts},
                    UploadId=multipart_upload["UploadId"],
                ),
            )
            logger.debug(multipart_upload_complete)
        except Exception:
            logger.error("JCDS2-UploadMultipart-Aborted %s", file_upload.path)
            multipart_aborted = await loop.run_in_executor(
                None,
                lambda: s3_client.abort_multipart_upload(
                    Bucket=multipart_upload["Bucket"],
                    Key=multipart_upload["Key"],
                    UploadId=multipart_upload["UploadId"],
                ),
            )
            logger.debug(multipart_aborted)
            raise

    @staticmethod
    async def _upload_part(
        s3_client, multipart_upload: dict, part_number: int, file_upload: FileUpload
    ):
        """Upload a single part of a multipart upload."""
        logger.info("JCDS2-UploadMultipart-Part %s %s", part_number, file_upload.path.name)
        loop = asyncio.get_event_loop()
        # TODO: Retry functionality if a part upload fails
        part_resp = await loop.run_in_executor(
            None,
            lambda: s3_client.upload_part(
                Body=file_upload.get_chunk(part_number - 1),
                Bucket=multipart_upload["Bucket"],
                Key=multipart_upload["Key"],
                PartNumber=part_number,
                UploadId=multipart_upload["UploadId"],
            ),
        )
        logger.debug(part_resp)
        return {"PartNumber": part_number, "ETag": part_resp["ETag"]}

    async def upload_file(self, file_path: str | Path) -> None:
        """Upload a file to the JCDS and create the package object asynchronously.

        If the file is less than 1 GiB in size the upload will be performed in a single request. If
        the file is greater than 1 GiB in size a multipart upload operation will be performed.

        A ``JCDS2FileExistsError`` is raised if any file of the same name exists and is associated to
        a package.

        .. important::

            This operation requires the ``aws`` extra dependency.

        :param file_path: The path to the file to upload. Will raise ``FileNotFoundError`` if the path
            to the file's location does not exist.
        :type file_path: str | Path
        """
        if not BOTO3_IS_INSTALLED:
            raise ImportError("The 'aws' extra dependency is required.")

        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError("A file or directory at the download path already exists")

        file_upload = FileUpload(file_path)

        packages = [
            await self.classic_api_client.get_package_by_id(p)
            for p in await self.classic_api_client.list_all_packages()
        ]

        for p in packages:
            if file_upload.path.name == p.filename:
                raise JCDS2FileExistsError(
                    f"The file '{file_upload.path.name}' exists and is associated to package ({p.id}) '{p.name}'"
                )

        new_jcds_file = await self.pro_api_client.create_jcds_file_v1()

        loop = asyncio.get_event_loop()
        boto3_session = await loop.run_in_executor(
            None,
            lambda: boto3.Session(
                aws_access_key_id=new_jcds_file.accessKeyID,
                aws_secret_access_key=new_jcds_file.secretAccessKey,
                aws_session_token=new_jcds_file.sessionToken,
                region_name=new_jcds_file.region,
            ),
        )

        s3_client = boto3_session.client(service_name="s3")

        try:
            # if file_upload.size < 5368709120:  # 5 GiB
            if file_upload.size < 1073741824:  # 1 GiB
                await self._upload_file(
                    s3_client=s3_client, jcds_file=new_jcds_file, file_upload=file_upload
                )
            else:
                await self._upload_multipart(
                    s3_client=s3_client, jcds_file=new_jcds_file, file_upload=file_upload
                )
        except Exception as err:
            logger.exception(err)
            raise
        else:
            new_package = ClassicPackage(name=file_path.name, filename=file_path.name)
            new_pkg_resp = await self.classic_api_client.create_package(data=new_package)
            logger.debug(new_pkg_resp)

    @staticmethod
    async def _download_range(async_client: httpx.AsyncClient, url: str, index: int, temp_dir: str):
        """Download a range of bytes from a URL."""
        range_start = index * CHUNK_SIZE
        range_end = ((index + 1) * CHUNK_SIZE) - 1
        async with async_client.get(
            url, headers={"Range": f"bytes={range_start}-{range_end}"}, timeout=60
        ) as range_response:
            range_response.raise_for_status()
            logger.debug(range_response.headers)
            with open(temp_dir + f"/chunk_{str(index).zfill(9)}", "wb") as fobj:
                fobj.write(range_response.content)

    async def download_file(self, file_name: str, download_path: str | Path) -> None:
        """Download a file from the JCDS by filename asynchronously.

        :param file_name: The name of the file in the JCDS to download.
        :type file_name: str

        :param download_path: The path to download the file to. If the provided path is directory
            the file name will be appended to it. Will raise `FileExistsError` if the path is to a
            file location that already exists.
        :type download_path: str | Path
        """
        if not isinstance(download_path, Path):
            download_path = Path(download_path)

        if download_path.is_dir():
            download_path = download_path / file_name

        if download_path.exists():
            raise FileExistsError("A file or directory at the download path already exists")

        try:
            download_file = await self.pro_api_client.get_jcds_file_v1(file_name=file_name)
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                raise JCDS2FileNotFoundError(f"The file '{file_name}' does not exist")
            else:
                raise

        # Create async client for downloads
        limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
        async_client = httpx.AsyncClient(limits=limits, timeout=httpx.Timeout(60))

        try:
            download_file_head = await async_client.head(download_file.uri)
            download_file_head.raise_for_status()
            total_chunks = math.ceil(int(download_file_head.headers["Content-Length"]) / CHUNK_SIZE)

            temp_dir = TemporaryDirectory(prefix="jcds2-download-")
            logger.debug("JCDS2-Download-TempDir %s", temp_dir.name)

            async for _ in self.concurrent_api_requests(
                handler=self._download_range,
                arguments=[
                    {
                        "async_client": async_client,
                        "url": download_file.uri,
                        "index": i,
                        "temp_dir": temp_dir.name,
                    }
                    for i in range(0, total_chunks)
                ],
                max_concurrency=5,
            ):
                pass

            with open(download_path, "ab") as fobj:
                for chunk in sorted(Path(temp_dir.name).glob("chunk_*")):
                    with open(chunk, "rb") as chunk_fobj:
                        fobj.write(chunk_fobj.read())
        finally:
            await async_client.aclose()

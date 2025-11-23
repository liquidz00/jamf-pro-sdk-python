import asyncio
import concurrent.futures
import logging
import tempfile
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    BinaryIO,
    Callable,
    Iterable,
    Iterator,
    Type,
)
from urllib.parse import urlunparse

import certifi
import httpx
from pydantic import BaseModel

from ..clients.classic_api import ClassicApi
from ..clients.jcds2 import JCDS2
from ..clients.pro_api import ProApi
from ..models.classic import ClassicApiModel
from ..models.client import SessionConfig
from .auth import CredentialsProvider

if TYPE_CHECKING:
    from ..clients.classic_api import AsyncClassicApi
    from ..clients.jcds2 import AsyncJCDS2
    from ..clients.pro_api import AsyncProApi

logger = logging.getLogger("jamf_pro_sdk")


class JamfProClient:
    def __init__(
        self,
        server: str,
        credentials: CredentialsProvider,
        port: int = 443,
        session_config: SessionConfig | None = None,
    ):
        """The base client class for interacting with the Jamf Pro APIs.

        Classic API, Pro API, and JCDS2 clients are instantiated with the base client.

        If the ``aws`` extra dependency is not installed the JCDS2 client will not be created.

        :param server: The hostname of the Jamf Pro server to connect to.
        :type server: str

        :param credentials: Accepts any credentials provider object to provide the
            username and password for initial authentication.
        :type credentials: CredentialsProvider

        :param port: The server port to connect over (defaults to `443`).
        :type port: int

        :param session_config: Pass a `SessionConfig` to configure session options.
        :type session_config: SessionConfig
        """
        self.session_config = SessionConfig() if not session_config else session_config

        self._credentials = credentials
        self._credentials.attach_client(self)
        self.get_access_token = self._credentials.get_access_token

        self.base_server_url = urlunparse(
            (
                self.session_config.scheme,
                f"{server}:{port}",
                "",
                None,
                None,
                None,
            )
        )

        self.session = self._setup_session()

        self.classic_api = ClassicApi(self.classic_api_request, self.concurrent_api_requests)
        self.pro_api = ProApi(self.pro_api_request, self.concurrent_api_requests)

        try:
            self.jcds2 = JCDS2(self.classic_api, self.pro_api, self.concurrent_api_requests)
        except ImportError:
            pass

    @staticmethod
    def _parse_cookie_file(cookie_file: str | Path) -> dict[str, str]:
        """Parse a cookies file and return a dictionary of key value pairs."""
        cookies = {}
        with open(cookie_file, "r") as fp:
            for line in fp:
                if line.startswith("#HttpOnly_"):
                    fields = line.strip().split()
                    cookies[fields[5]] = fields[6]
        return cookies

    @staticmethod
    def _load_ca_cert_bundle(ca_cert_bundle_path: str | Path):
        """Create a copy of the certifi trust store and append the passed CA cert bundle in a
        temporary file.
        """
        with open(certifi.where(), "r") as f_obj:
            current_ca_cert = f_obj.read()

        with open(ca_cert_bundle_path, "r") as f_obj:
            ca_cert_bundle = f_obj.read()

        temp_ca_cert_dir = tempfile.mkdtemp(prefix="jamf-pro-sdk-")
        temp_ca_cert = f"{temp_ca_cert_dir}/cacert.pem"

        with open(temp_ca_cert, "w") as f_obj:
            f_obj.write(current_ca_cert)
            f_obj.write(ca_cert_bundle)

        return temp_ca_cert

    def _setup_session(self) -> httpx.Client:
        """Set up the httpx client session."""
        limits = httpx.Limits(
            max_connections=self.session_config.max_concurrency,
            max_keepalive_connections=self.session_config.max_concurrency,
        )
        timeout = (
            httpx.Timeout(self.session_config.timeout) if self.session_config.timeout else None
        )

        verify = True
        if self.session_config.verify and self.session_config.ca_cert_bundle is not None:
            verify = self._load_ca_cert_bundle(self.session_config.ca_cert_bundle)
        elif not self.session_config.verify:
            verify = False

        cookies = None
        if self.session_config.cookie:
            cookies = self._parse_cookie_file(self.session_config.cookie)

        # httpx doesn't have built-in retry, so we'll handle it at the request level if needed
        return httpx.Client(
            limits=limits,
            timeout=timeout,
            verify=verify,
            cookies=cookies,
            headers={"Accept": "application/json", "User-Agent": self.session_config.user_agent},
        )

    def classic_api_request(
        self,
        method: str,
        resource_path: str,
        data: str | ClassicApiModel | None = None,
        override_headers: dict | None = None,
    ) -> httpx.Response:
        """Perform a request to the Classic API.

        :param method: The HTTP method. Allowed values (case-insensitive) are: GET, POST,
            PUT, and DELETE.
        :type method: str

        :param resource_path: The path of the API being requested that comes `after`
            ``JSSResource``.
        :type resource_path: str

        :param data: If the request is a ``POST`` or ``PUT``, the XML string or
            ``ClassicApiModel`` that is being sent.
        :type data: str | ClassicApiModel

        :param override_headers: A dictionary of key-value pairs that will be set as
            headers for the request. You cannot override the ``Authorization`` or
            ``Content-Type`` headers.
        :type override_headers: dict[str, str]

        :return: `httpx Response <https://www.python-httpx.org/api/#response>`_ object
        :rtype: httpx.Response
        """
        headers = {"Authorization": f"Bearer {self._credentials.get_access_token()}"}

        if override_headers:
            headers.update(override_headers)

        content = None
        if data and (method.lower() in ("post", "put")):
            headers["Content-Type"] = "text/xml"
            content = data if isinstance(data, str) else data.xml(exclude_read_only=True)

        capi_resp = self.session.request(
            method=method,
            url=f"{self.base_server_url}/JSSResource/{resource_path}",
            headers=headers,
            content=content,
        )

        logger.info("ClassicAPIRequest %s %s", method.upper(), resource_path)
        try:
            capi_resp.raise_for_status()
        except httpx.HTTPStatusError:
            # TODO: XML error response parser
            logger.error(capi_resp.text)
            raise

        return capi_resp

    def pro_api_request(
        self,
        method: str,
        resource_path: str,
        query_params: dict[str, str] | None = None,
        data: dict | BaseModel | None = None,
        files: dict[str, tuple[str, BinaryIO, str]] | None = None,
        override_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Perform a request to the Pro API.

        :param method: The HTTP method. Allowed values (case-insensitive) are: GET, POST,
            PUT, PATCH, and DELETE.
        :type method: str

        :param resource_path: The path of the API being requested that comes `after`
            ``api``. Include the API version at the beginning of the resource path.
        :type resource_path: str

        :param query_params: Query string parameters to be included with the request URL string.
        :type query_params: dict[str, str]

        :param data: If the request is a ``POST``, ``PUT``, or ``PATCH``, the dictionary
            or ``BaseModel`` that is being sent.
        :type data: dict | BaseModel

        :param files: If the request is a ``POST``, a dictionary with a single ``files`` key,
            and a tuple containing the filename, file-like object to upload, and mime type.
        :type files: dict[str, tuple[str, BinaryIO, str]] | None

        :param override_headers: A dictionary of key-value pairs that will be set as
            headers for the request. You cannot override the ``Authorization`` or
            ``Content-Type`` headers.
        :type override_headers: dict[str, str]

        :return: `httpx Response <https://www.python-httpx.org/api/#response>`_ object
        :rtype: httpx.Response
        """
        headers = {"Authorization": f"Bearer {self._credentials.get_access_token()}"}

        if override_headers:
            headers.update(override_headers)

        json_data = None
        content_data = None
        if data and (method.lower() in ("post", "put", "patch")):
            headers["Content-Type"] = "application/json"
            if isinstance(data, dict):
                json_data = data
            elif isinstance(data, BaseModel):
                content_data = data.model_dump_json(exclude_none=True)
            else:
                raise ValueError("'data' must be one of 'dict' or 'BaseModel'")

        files_data = None
        if files and (method.lower() == "post"):
            files_data = files

        pro_resp = self.session.request(
            method=method,
            url=f"{self.base_server_url}/api/{resource_path}",
            headers=headers,
            params=query_params,
            json=json_data,
            content=content_data,
            files=files_data,
        )

        logger.info("ProAPIRequest %s %s", method.upper(), resource_path)
        try:
            pro_resp.raise_for_status()
        except httpx.HTTPStatusError:
            logger.error(pro_resp.text)
            raise

        return pro_resp

    def concurrent_api_requests(
        self,
        handler: Callable,
        arguments: Iterable[Any],
        return_model: Type[BaseModel] | None = None,
        max_concurrency: int | None = None,
        return_exceptions: bool | None = None,
    ) -> Iterator[Any | Exception]:
        """An interface for performing concurrent API operations.

        :param handler: The method that will be called.
        :type handler: Callable

        :param arguments: An iterable object containing the arguments to be passed to the
            ``handler``. If the items within the iterable are dictionaries (``dict``) they
            will be unpacked when passed. Use this to pass multiple arguments.
        :type arguments: Iterable[Any]

        :param return_model: The Pydantic model that should be instantiated from the responses. The
            model will only be returned if the response from the ``handler`` is not also a model. If
            it is the ``return_model`` is ignored. The response MUST be a JSON body for this option
            to succeed.
        :type return_model: BaseModel

        :param max_concurrency: An override the value for ``session_config.max_concurrency``. Note:
            this override `cannot` be higher than ``session_config.max_concurrency``.
        :type max_concurrency: int

        :param return_exceptions: If an exception is encountered by the ``handler`` the
            iterator will continue without a yield. Setting this to ``True`` will return the
            exception object. If not set, the value for ``session_config.return_exceptions`` is
            used.
        :type return_exceptions: bool

        :return: An iterator that will yield the result for each operation.
        :rtype: Iterator

        """
        if return_exceptions is None:
            return_exceptions = self.session_config.return_exceptions

        if max_concurrency:
            max_concurrency = min(max_concurrency, self.session_config.max_concurrency)
        else:
            max_concurrency = self.session_config.max_concurrency

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            logger.info("ConcurrentAPIRequest %s ", handler.__name__)
            executor_results = list()
            for i in arguments:
                if isinstance(i, dict):
                    executor_results.append(executor.submit(handler, **i))
                else:
                    executor_results.append(executor.submit(handler, i))

            concurrent.futures.wait(executor_results)

        for result in executor_results:
            try:
                response = result.result()
                if isinstance(response, BaseModel):
                    yield response
                elif isinstance(response, httpx.Response) and return_model:
                    response_data = (
                        response.json()[return_model._xml_root_name]
                        if hasattr(return_model, "_xml_root_name")
                        else response.json()
                    )
                    yield return_model.model_validate(response_data)
                else:
                    yield response
            except Exception as err:
                logger.warning(err)
                if return_exceptions:
                    yield err
                else:
                    continue


class AsyncJamfProClient:
    """The async client class for interacting with the Jamf Pro APIs.

    Classic API, Pro API, and JCDS2 clients are instantiated with the base client.

    If the ``aws`` extra dependency is not installed the JCDS2 client will not be created.

    :param server: The hostname of the Jamf Pro server to connect to.
    :type server: str

    :param credentials: Accepts any credentials provider object to provide the
        username and password for initial authentication.
    :type credentials: CredentialsProvider

    :param port: The server port to connect over (defaults to `443`).
    :type port: int

    :param session_config: Pass a `SessionConfig` to configure session options.
    :type session_config: SessionConfig
    """

    def __init__(
        self,
        server: str,
        credentials: CredentialsProvider,
        port: int = 443,
        session_config: SessionConfig | None = None,
    ):
        self.session_config = SessionConfig() if not session_config else session_config

        self._credentials = credentials
        self._credentials.attach_async_client(self)
        self.get_access_token_async = self._credentials.get_access_token_async

        self.base_server_url = urlunparse(
            (
                self.session_config.scheme,
                f"{server}:{port}",
                "",
                None,
                None,
                None,
            )
        )

        self.async_client = self._setup_async_client()

        # Import here to avoid circular imports
        from ..clients.classic_api import AsyncClassicApi
        from ..clients.pro_api import AsyncProApi

        self.classic_api = AsyncClassicApi(
            self.async_classic_api_request, self.async_concurrent_api_requests
        )
        self.pro_api = AsyncProApi(self.async_pro_api_request, self.async_concurrent_api_requests)

        try:
            from ..clients.jcds2 import AsyncJCDS2

            self.jcds2 = AsyncJCDS2(
                self.classic_api, self.pro_api, self.async_concurrent_api_requests
            )
        except ImportError:
            pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.async_client.aclose()

    @staticmethod
    def _parse_cookie_file(cookie_file: str | Path) -> dict[str, str]:
        """Parse a cookies file and return a dictionary of key value pairs."""
        cookies = {}
        with open(cookie_file, "r") as fp:
            for line in fp:
                if line.startswith("#HttpOnly_"):
                    fields = line.strip().split()
                    cookies[fields[5]] = fields[6]
        return cookies

    @staticmethod
    def _load_ca_cert_bundle(ca_cert_bundle_path: str | Path):
        """Create a copy of the certifi trust store and append the passed CA cert bundle in a
        temporary file.
        """
        with open(certifi.where(), "r") as f_obj:
            current_ca_cert = f_obj.read()

        with open(ca_cert_bundle_path, "r") as f_obj:
            ca_cert_bundle = f_obj.read()

        temp_ca_cert_dir = tempfile.mkdtemp(prefix="jamf-pro-sdk-")
        temp_ca_cert = f"{temp_ca_cert_dir}/cacert.pem"

        with open(temp_ca_cert, "w") as f_obj:
            f_obj.write(current_ca_cert)
            f_obj.write(ca_cert_bundle)

        return temp_ca_cert

    def _setup_async_client(self) -> httpx.AsyncClient:
        """Set up the async HTTP client."""
        limits = httpx.Limits(
            max_connections=self.session_config.max_concurrency,
            max_keepalive_connections=self.session_config.max_concurrency,
        )
        timeout = (
            httpx.Timeout(self.session_config.timeout) if self.session_config.timeout else None
        )

        verify = True
        if self.session_config.verify and self.session_config.ca_cert_bundle is not None:
            verify = self._load_ca_cert_bundle(self.session_config.ca_cert_bundle)
        elif not self.session_config.verify:
            verify = False

        cookies = None
        if self.session_config.cookie:
            cookies = self._parse_cookie_file(self.session_config.cookie)

        return httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            verify=verify,
            cookies=cookies,
            headers={"Accept": "application/json", "User-Agent": self.session_config.user_agent},
        )

    async def async_classic_api_request(
        self,
        method: str,
        resource_path: str,
        data: str | ClassicApiModel | None = None,
        override_headers: dict | None = None,
    ) -> httpx.Response:
        """Perform an async request to the Classic API.

        :param method: The HTTP method. Allowed values (case-insensitive) are: GET, POST,
            PUT, and DELETE.
        :type method: str

        :param resource_path: The path of the API being requested that comes `after`
            ``JSSResource``.
        :type resource_path: str

        :param data: If the request is a ``POST`` or ``PUT``, the XML string or
            ``ClassicApiModel`` that is being sent.
        :type data: str | ClassicApiModel

        :param override_headers: A dictionary of key-value pairs that will be set as
            headers for the request. You cannot override the ``Authorization`` or
            ``Content-Type`` headers.
        :type override_headers: dict[str, str]

        :return: `httpx Response <https://www.python-httpx.org/api/#response>`_ object
        :rtype: httpx.Response
        """
        access_token = await self._credentials.get_access_token_async()
        headers = {"Authorization": f"Bearer {access_token.token}"}

        if override_headers:
            headers.update(override_headers)

        if data and (method.lower() in ("post", "put")):
            headers["Content-Type"] = "text/xml"
            data_content = data if isinstance(data, str) else data.xml(exclude_read_only=True)
        else:
            data_content = None

        resp = await self.async_client.request(
            method=method,
            url=f"{self.base_server_url}/JSSResource/{resource_path}",
            headers=headers,
            content=data_content,
        )

        logger.info("ClassicAPIRequest %s %s", method.upper(), resource_path)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            # TODO: XML error response parser
            logger.error(resp.text)
            raise

        return resp

    async def async_pro_api_request(
        self,
        method: str,
        resource_path: str,
        query_params: dict[str, str] | None = None,
        data: dict | BaseModel | None = None,
        files: dict[str, tuple[str, BinaryIO, str]] | None = None,
        override_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Perform an async request to the Pro API.

        :param method: The HTTP method. Allowed values (case-insensitive) are: GET, POST,
            PUT, PATCH, and DELETE.
        :type method: str

        :param resource_path: The path of the API being requested that comes `after`
            ``api``. Include the API version at the beginning of the resource path.
        :type resource_path: str

        :param query_params: Query string parameters to be included with the request URL string.
        :type query_params: dict[str, str]

        :param data: If the request is a ``POST``, ``PUT``, or ``PATCH``, the dictionary
            or ``BaseModel`` that is being sent.
        :type data: dict | BaseModel

        :param files: If the request is a ``POST``, a dictionary with a single ``files`` key,
            and a tuple containing the filename, file-like object to upload, and mime type.
        :type files: dict[str, tuple[str, BinaryIO, str]] | None

        :param override_headers: A dictionary of key-value pairs that will be set as
            headers for the request. You cannot override the ``Authorization`` or
            ``Content-Type`` headers.
        :type override_headers: dict[str, str]

        :return: `httpx Response <https://www.python-httpx.org/api/#response>`_ object
        :rtype: httpx.Response
        """
        access_token = await self._credentials.get_access_token_async()
        headers = {"Authorization": f"Bearer {access_token.token}"}

        if override_headers:
            headers.update(override_headers)

        if data and (method.lower() in ("post", "put", "patch")):
            headers["Content-Type"] = "application/json"
            if isinstance(data, dict):
                json_data = data
                content_data = None
            elif isinstance(data, BaseModel):
                json_data = None
                content_data = data.model_dump_json(exclude_none=True)
            else:
                raise ValueError("'data' must be one of 'dict' or 'BaseModel'")
        else:
            json_data = None
            content_data = None

        files_data = None
        if files and (method.lower() == "post"):
            files_data = files

        resp = await self.async_client.request(
            method=method,
            url=f"{self.base_server_url}/api/{resource_path}",
            headers=headers,
            params=query_params,
            json=json_data,
            content=content_data,
            files=files_data,
        )

        logger.info("ProAPIRequest %s %s", method.upper(), resource_path)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            logger.error(resp.text)
            raise

        return resp

    async def async_concurrent_api_requests(
        self,
        handler: Callable,
        arguments: Iterable[Any],
        return_model: Type[BaseModel] | None = None,
        max_concurrency: int | None = None,
        return_exceptions: bool | None = None,
    ) -> AsyncIterator[Any | Exception]:
        """An async interface for performing concurrent API operations.

        :param handler: The async method that will be called.
        :type handler: Callable

        :param arguments: An iterable object containing the arguments to be passed to the
            ``handler``. If the items within the iterable are dictionaries (``dict``) they
            will be unpacked when passed. Use this to pass multiple arguments.
        :type arguments: Iterable[Any]

        :param return_model: The Pydantic model that should be instantiated from the responses. The
            model will only be returned if the response from the ``handler`` is not also a model. If
            it is the ``return_model`` is ignored. The response MUST be a JSON body for this option
            to succeed.
        :type return_model: BaseModel

        :param max_concurrency: An override the value for ``session_config.max_concurrency``. Note:
            this override `cannot` be higher than ``session_config.max_concurrency``.
        :type max_concurrency: int

        :param return_exceptions: If an exception is encountered by the ``handler`` the
            iterator will continue without a yield. Setting this to ``True`` will return the
            exception object. If not set, the value for ``session_config.return_exceptions`` is
            used.
        :type return_exceptions: bool

        :return: An async iterator that will yield the result for each operation.
        :rtype: AsyncIterator
        """
        if return_exceptions is None:
            return_exceptions = self.session_config.return_exceptions

        if max_concurrency:
            max_concurrency = min(max_concurrency, self.session_config.max_concurrency)
        else:
            max_concurrency = self.session_config.max_concurrency

        # Convert arguments to list for processing
        args_list = list(arguments)

        async def call_handler(arg):
            """Call the handler with the given argument."""
            try:
                if isinstance(arg, dict):
                    return await handler(**arg)
                else:
                    return await handler(arg)
            except Exception as err:
                if return_exceptions:
                    return err
                else:
                    logger.warning(err)
                    return None

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrency)

        async def bounded_call_handler(arg):
            """Call handler with semaphore limit."""
            async with semaphore:
                return await call_handler(arg)

        logger.info("ConcurrentAPIRequest %s ", handler.__name__)

        # Create tasks for all arguments
        tasks = [bounded_call_handler(arg) for arg in args_list]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)

        # Process and yield results
        for result in results:
            if result is None and not return_exceptions:
                continue
            if isinstance(result, BaseModel):
                yield result
            elif isinstance(result, httpx.Response) and return_model:
                response_data = (
                    result.json()[return_model._xml_root_name]
                    if hasattr(return_model, "_xml_root_name")
                    else result.json()
                )
                yield return_model.model_validate(response_data)
            else:
                yield result

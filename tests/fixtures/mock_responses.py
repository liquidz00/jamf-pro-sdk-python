"""Mock API response data for testing."""

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx


def create_mock_token_response(token_type: str = "user") -> dict[str, Any]:
    """
    Create a mock access token response.

    :param token_type: Type of token ('user' or 'oauth')
    :type token_type: str
    :return: Mock token response dictionary
    :rtype: dict[str, Any]
    """
    expires = datetime.now(timezone.utc) + timedelta(seconds=3600)
    if token_type == "user":
        return {
            "token": "mock_user_token_12345",
            "expires": expires.isoformat(),
        }
    else:  # oauth
        return {
            "access_token": "mock_oauth_token_12345",
            "expires_in": 3600,
            "scope": "read write",
        }


def create_mock_httpx_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
    text: str | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """
    Create a mock httpx.Response object.

    :param status_code: HTTP status code
    :type status_code: int
    :param json_data: JSON data to return
    :type json_data: dict[str, Any] | None
    :param text: Text content to return
    :type text: str | None
    :param headers: Response headers
    :type headers: dict[str, str] | None
    :return: Mock httpx.Response
    :rtype: httpx.Response
    """
    import json

    response_headers = headers or {}
    if json_data:
        content = json.dumps(json_data).encode()
        response_headers.setdefault("Content-Type", "application/json")
    elif text:
        content = text.encode()
    else:
        content = b""

    request = httpx.Request("GET", "https://example.com")
    return httpx.Response(
        status_code=status_code,
        headers=response_headers,
        content=content,
        request=request,
    )


def create_mock_classic_api_response(
    resource_name: str, data: dict[str, Any] | list[dict[str, Any]]
) -> httpx.Response:
    """
    Create a mock Classic API response.

    :param resource_name: Name of the resource (e.g., 'categories', 'computers')
    :type resource_name: str
    :param data: Response data
    :type data: dict[str, Any] | list[dict[str, Any]]
    :return: Mock httpx.Response
    :rtype: httpx.Response
    """
    if isinstance(data, list):
        response_data = {resource_name: data}
    else:
        response_data = {resource_name: data}
    return create_mock_httpx_response(json_data=response_data)


def create_mock_pro_api_response(data: dict[str, Any] | list[dict[str, Any]]) -> httpx.Response:
    """
    Create a mock Pro API response.

    :param data: Response data
    :type data: dict[str, Any] | list[dict[str, Any]]
    :return: Mock httpx.Response
    :rtype: httpx.Response
    """
    return create_mock_httpx_response(
        json_data=data if isinstance(data, dict) else {"results": data}
    )

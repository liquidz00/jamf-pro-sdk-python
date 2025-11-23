Async Usage
===========

The SDK provides full asynchronous support through the :class:`~jamf_pro_sdk.clients.AsyncJamfProClient` class and async versions of all API clients. Async operations are ideal for I/O-bound workloads where you need to make many concurrent API requests efficiently.

.. note::

    If you're new to asynchronous programming in Python, the SDK's async interface uses the standard ``asyncio`` library and follows common Python async patterns with ``async``/``await`` syntax.

When to Use Async
-----------------

Consider using the async client when:

* Making multiple API requests concurrently
* Building web applications or services with async frameworks (FastAPI, aiohttp, etc.)
* MCP Server development or usage
* Integrating with other async libraries or services
* Optimizing I/O-bound operations for better performance

The synchronous :class:`~jamf_pro_sdk.clients.JamfProClient` is perfectly suitable for:

* Scripts and automation tasks
* Simple sequential operations
* Applications where threading is acceptable

Creating an Async Client
-------------------------

Create an async client object using the same credentials providers as the synchronous client:

.. code-block:: python

    >>> import asyncio
    >>> from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    >>> 
    >>> async def main():
    ...     client = AsyncJamfProClient(
    ...         server="jamf.my.org",
    ...         credentials=ApiClientCredentialsProvider("client_id", "client_secret")
    ...     )
    ...     # Use the client
    ...     computers = await client.pro_api.get_computer_inventory_v1()
    ...     return computers
    ...
    >>> asyncio.run(main())
    [Computer(id='117', udid='a311b7c8-75ee-48cf-9b1b-a8598f013366', ...]
    >>>

.. note::

    When passing your Jamf Pro server name, do not include the scheme (``https://``) as the SDK handles this automatically for you.

Using Context Managers
^^^^^^^^^^^^^^^^^^^^^^

The recommended approach is to use the async context manager which ensures proper cleanup of resources:

.. code-block:: python

    >>> import asyncio
    >>> from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    >>> 
    >>> async def main():
    ...     async with AsyncJamfProClient(
    ...         server="jamf.my.org",
    ...         credentials=ApiClientCredentialsProvider("client_id", "client_secret")
    ...     ) as client:
    ...         computers = await client.pro_api.get_computer_inventory_v1()
    ...         return computers
    ...
    >>> asyncio.run(main())
    [Computer(id='117', udid='a311b7c8-75ee-48cf-9b1b-a8598f013366', ...]
    >>>

.. tip::

    Using ``async with`` automatically closes the underlying HTTP client when exiting the context, preventing resource leaks.

Basic Async/Await Patterns
---------------------------

All API operations that are available synchronously have async equivalents. The async methods follow the same naming and parameter conventions.

Classic API Operations
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> import asyncio
    >>> from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    >>> 
    >>> async def get_computers():
    ...     async with AsyncJamfProClient(
    ...         server="jamf.my.org",
    ...         credentials=ApiClientCredentialsProvider("client_id", "client_secret")
    ...     ) as client:
    ...         # List all computers
    ...         computers = await client.classic_api.list_all_computers()
    ...         
    ...         # Get a specific computer
    ...         computer = await client.classic_api.get_computer_by_id(1)
    ...         
    ...         return computers, computer
    ...
    >>> asyncio.run(get_computers())
    ([ComputersItem(id=1, name="Oscar's MacBook Air", ...), ...], Computer(...))
    >>>

Pro API Operations
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> import asyncio
    >>> from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    >>> from jamf_pro_sdk.clients.pro_api.pagination import FilterField
    >>> 
    >>> async def get_filtered_computers():
    ...     async with AsyncJamfProClient(
    ...         server="jamf.my.org",
    ...         credentials=ApiClientCredentialsProvider("client_id", "client_secret")
    ...     ) as client:
    ...         # Get computer inventory with filtering
    ...         filter_expr = FilterField("general.name").eq("Oscar's MacBook Air")
    ...         computers = await client.pro_api.get_computer_inventory_v1(
    ...             filter_expression=filter_expr
    ...         )
    ...         return computers
    ...
    >>> asyncio.run(get_filtered_computers())
    [Computer(id='1', general=ComputerGeneral(name="Oscar's MacBook Air", ...), ...)]
    >>>

Async Pagination
^^^^^^^^^^^^^^^^

Paginated requests work seamlessly with async operations. The paginator will automatically fetch all pages concurrently:

.. code-block:: python

    >>> import asyncio
    >>> from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    >>> 
    >>> async def get_all_computers():
    ...     async with AsyncJamfProClient(
    ...         server="jamf.my.org",
    ...         credentials=ApiClientCredentialsProvider("client_id", "client_secret")
    ...     ) as client:
    ...         # Returns all results automatically
    ...         computers = await client.pro_api.get_computer_inventory_v1(page_size=100)
    ...         return computers
    ...
    >>> asyncio.run(get_all_computers())
    [Computer(...), Computer(...), ...]
    >>>

You can also iterate over pages asynchronously using the generator:

.. code-block:: python

    >>> import asyncio
    >>> from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    >>> 
    >>> async def process_computers_by_page():
    ...     async with AsyncJamfProClient(
    ...         server="jamf.my.org",
    ...         credentials=ApiClientCredentialsProvider("client_id", "client_secret")
    ...     ) as client:
    ...         # Get generator for page-by-page iteration
    ...         pages = await client.pro_api.get_computer_inventory_v1(
    ...             page_size=100,
    ...             return_generator=True
    ...         )
    ...         
    ...         async for page in pages:
    ...             for computer in page.results:
    ...                 print(f"Processing {computer.general.name}")
    ...
    >>> asyncio.run(process_computers_by_page())
    Processing Oscar's MacBook Air
    Processing Chip's MacBook Pro
    ...
    >>>

Performing Concurrent Operations
---------------------------------

One of the primary benefits of async is the ability to perform many operations concurrently. The async client provides the :meth:`~jamf_pro_sdk.clients.AsyncJamfProClient.async_concurrent_api_requests` method for this purpose.

Concurrent Reads
^^^^^^^^^^^^^^^^

Here's an example of reading multiple computer records concurrently:

.. code-block:: python

    import asyncio
    from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider

    async def main():
        async with AsyncJamfProClient(
            server="jamf.my.org",
            credentials=ApiClientCredentialsProvider("client_id", "client_secret")
        ) as client:
            # Get list of all computer IDs
            all_computers = await client.classic_api.list_all_computers()
            computer_ids = [c.id for c in all_computers]
            
            # Fetch all computer details concurrently
            async for computer in client.async_concurrent_api_requests(
                handler=client.classic_api.get_computer_by_id,
                arguments=computer_ids
            ):
                print(f"{computer.general.id}: {computer.general.name}")
    
    asyncio.run(main())

The ``handler`` is any async callable function, and ``arguments`` can be any iterable where each item is passed to the handler.

.. tip::

    The default concurrency limit is 5 (following Jamf's best practices). You can adjust this using the ``max_concurrency`` parameter in :class:`~jamf_pro_sdk.models.client.SessionConfig`.

Concurrent Operations with Multiple Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your handler requires multiple arguments, pass dictionaries that will be unpacked:

.. code-block:: python

    import asyncio
    from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider

    async def main():
        async with AsyncJamfProClient(
            server="jamf.my.org",
            credentials=ApiClientCredentialsProvider("client_id", "client_secret")
        ) as client:
            # Prepare arguments as dictionaries
            args = [
                {"method": "get", "resource_path": f"computers/id/{id}"}
                for id in [1, 2, 3, 4, 5]
            ]
            
            # Make concurrent requests
            async for response in client.async_concurrent_api_requests(
                handler=client.async_classic_api_request,
                arguments=args
            ):
                print(f"Response: {response.status_code}")

    asyncio.run(main())

Custom Async Functions
^^^^^^^^^^^^^^^^^^^^^^

You can wrap complex logic into custom async functions and use them with concurrent operations:

.. code-block:: python

    import asyncio
    from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    from jamf_pro_sdk.models.classic.computers import ClassicComputer

    async def update_computer_building(client, computer_id, new_building):
        """Read a computer and update its building if needed."""
        current = await client.classic_api.get_computer_by_id(
            computer_id,
            subsets=["location"]
        )
        
        if current.location.building != new_building:
            update = ClassicComputer()
            update.location.building = new_building
            await client.classic_api.update_computer_by_id(computer_id, update)
            return f"Updated computer {computer_id}"
        return f"Skipped computer {computer_id}"

    async def main():
        async with AsyncJamfProClient(
            server="jamf.my.org",
            credentials=ApiClientCredentialsProvider("client_id", "client_secret")
        ) as client:
            # Create a wrapper that includes the client and new building
            async def wrapper(computer_id):
                return await update_computer_building(client, computer_id, "Main Office")
            
            # Process multiple computers concurrently
            computer_ids = [1, 2, 3, 4, 5]
            async for result in client.async_concurrent_api_requests(
                handler=wrapper,
                arguments=computer_ids
            ):
                print(result)

    asyncio.run(main())

Error Handling
--------------

Error handling in async code follows standard Python exception handling with ``try``/``except`` blocks:

Basic Error Handling
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    >>> import asyncio
    >>> from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    >>> from jamf_pro_sdk.exceptions import JamfProAPIError
    >>> 
    >>> async def safe_get_computer():
    ...     async with AsyncJamfProClient(
    ...         server="jamf.my.org",
    ...         credentials=ApiClientCredentialsProvider("client_id", "client_secret")
    ...     ) as client:
    ...         try:
    ...             computer = await client.classic_api.get_computer_by_id(999999)
    ...             return computer
    ...         except JamfProAPIError as e:
    ...             print(f"API Error: {e}")
    ...             return None
    ...
    >>> asyncio.run(safe_get_computer())
    API Error: ...
    None
    >>>

Handling Errors in Concurrent Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, the first exception in concurrent operations will be raised. You can use the ``return_exceptions`` parameter in :class:`~jamf_pro_sdk.models.client.SessionConfig` to collect exceptions instead:

.. code-block:: python

    import asyncio
    from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider, SessionConfig

    async def main():
        session_config = SessionConfig(return_exceptions=True)
        
        async with AsyncJamfProClient(
            server="jamf.my.org",
            credentials=ApiClientCredentialsProvider("client_id", "client_secret"),
            session_config=session_config
        ) as client:
            # Some IDs may not exist
            computer_ids = [1, 2, 999999, 4, 5]
            
            async for result in client.async_concurrent_api_requests(
                handler=client.classic_api.get_computer_by_id,
                arguments=computer_ids
            ):
                if isinstance(result, Exception):
                    print(f"Error: {result}")
                else:
                    print(f"Success: {result.general.name}")

    asyncio.run(main())

Access Tokens
-------------

Access token management works similarly to the synchronous client. The async client automatically handles token retrieval, caching, and refresh:

.. code-block:: python

    >>> import asyncio
    >>> from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    >>> 
    >>> async def get_token():
    ...     async with AsyncJamfProClient(
    ...         server="jamf.my.org",
    ...         credentials=ApiClientCredentialsProvider("client_id", "client_secret")
    ...     ) as client:
    ...         access_token = await client.get_access_token_async()
    ...         return access_token
    ...
    >>> token = asyncio.run(get_token())
    >>> token
    AccessToken(type='user', token='eyJhbGciOiJIUzI1NiJ9...', expires=datetime.datetime(2023, 8, 21, 16, 57, 1, 113000, tzinfo=datetime.timezone.utc), scope=None)
    >>> token.token
    'eyJhbGciOiJIUzI1NiJ9.eyJhdXRoZW50aWNhdGVkLWFwcCI6IkdFTkVSSUMi...'
    >>>

Configuring the Async Client
-----------------------------

The async client accepts the same :class:`~jamf_pro_sdk.models.client.SessionConfig` as the synchronous client:

.. code-block:: python

    >>> import asyncio
    >>> from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider, SessionConfig
    >>> 
    >>> async def main():
    ...     config = SessionConfig(
    ...         timeout=30,
    ...         max_concurrency=10,
    ...         verify=True
    ...     )
    ...     
    ...     async with AsyncJamfProClient(
    ...         server="jamf.my.org",
    ...         credentials=ApiClientCredentialsProvider("client_id", "client_secret"),
    ...         session_config=config
    ...     ) as client:
    ...         computers = await client.pro_api.get_computer_inventory_v1()
    ...         return computers
    ...
    >>> asyncio.run(main())
    [Computer(...), ...]
    >>>

.. note::

    The ``max_concurrency`` setting controls the connection pool size and the concurrency limit for :meth:`~jamf_pro_sdk.clients.AsyncJamfProClient.async_concurrent_api_requests`.

    The Jamf Developer Guide recommends not exceeding 5 concurrent connections. Read more about scalability with the Jamf Pro APIs `here <https://developer.jamf.com/developer-guide/docs/jamf-pro-api-scalability-best-practices>`_.

Logging
-------

Logging works the same way with async operations. You can use the provided :func:`~jamf_pro_sdk.helpers.logger_quick_setup` function:

.. code-block:: python

    import asyncio
    import logging
    from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    from jamf_pro_sdk.helpers import logger_quick_setup

    logger_quick_setup(level=logging.DEBUG)

    async def main():
        async with AsyncJamfProClient(
            server="jamf.my.org",
            credentials=ApiClientCredentialsProvider("client_id", "client_secret")
        ) as client:
            computers = await client.pro_api.get_computer_inventory_v1()
            return computers

    asyncio.run(main())

The logger will output debug information for all async operations just as it does for synchronous ones.

Integration with Async Frameworks
----------------------------------

The async client integrates seamlessly with popular async frameworks:

FastAPI Example
^^^^^^^^^^^^^^^

.. code-block:: python

    from fastapi import FastAPI, Depends
    from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider

    app = FastAPI()

    async def get_jamf_client():
        """Dependency to provide Jamf Pro client."""
        async with AsyncJamfProClient(
            server="jamf.my.org",
            credentials=ApiClientCredentialsProvider("client_id", "client_secret")
        ) as client:
            yield client

    @app.get("/computers")
    async def list_computers(client: AsyncJamfProClient = Depends(get_jamf_client)):
        """List all computers from Jamf Pro."""
        computers = await client.classic_api.list_all_computers()
        return [{"id": c.id, "name": c.name} for c in computers]

    @app.get("/computers/{computer_id}")
    async def get_computer(
        computer_id: int,
        client: AsyncJamfProClient = Depends(get_jamf_client)
    ):
        """Get a specific computer by ID."""
        computer = await client.classic_api.get_computer_by_id(computer_id)
        return computer.dict()

See Also
--------

* :doc:`/reference/clients_async` - Async client reference documentation
* :doc:`/reference/clients_pro_async` - Async Pro API client reference
* :doc:`/reference/clients_classic_async` - Async Classic API client reference
* :doc:`/user/advanced` - Advanced usage patterns including concurrent operations


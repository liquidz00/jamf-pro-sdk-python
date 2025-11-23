Advanced Usage
==============

Custom Credentials Providers
----------------------------

A :class:`~jamf_pro_sdk.clients.auth.CredentialsProvider` is an interface for the SDK to obtain access tokens. The SDK comes with a number of built-in options that are detailed in the :doc:`/reference/credentials` reference. You can create your own provider by inheriting from the ``CredentialsProvider`` base class and overriding the ``_refresh_access_token`` method.

The following example does not accept a username or password and retrieves a token from a DynamoDB table in an AWS account (it is assumed an external process is managing this table entry).

.. code-block:: python

    >>> import boto3
    >>> from jamf_pro_sdk.clients.auth import CredentialsProvider
    >>> from jamf_pro_sdk.models.client import AccessToken
    >>>
    >>> class DynamoDBProvider(CredentialsProvider):
    ...     def __init__(self, table_name: str):
    ...         self.table = boto3.resource("dynamodb").Table(table_name)
    ...         super().__init__()
    ...     @property
    ...     def _request_access_token(self) -> AccessToken:
    ...         item = table.get_item(Key={"pk": "access-token"})["Item"]
    ...         return AccessToken(type="user", token=item["token"], expires=item["expires"])
    ...
    >>> creds = DynamoDBProvider("my-table")
    >>> creds.get_access_token()
    AccessToken(type='user', token='eyJhbGciOiJIUzI1NiJ9...' ...)
    >>>

The built-in providers retrieve and store the username and password values on initialization, but by leveraging the override method shown above you can write providers that read/cache from remote locations on each invoke.

Using Unsupported APIs
----------------------

The SDK's clients provide curated methods to a large number of Jamf Pro APIs. Not all APIs may be implemented, and newer APIs may not be accounted for. You can still leverage the client to request any API without using the curated methods while still taking advantage of the client's session features and token management.

Here is the built-in method for getting a computer from the Classic API:

.. code-block:: python

    >>> computer = client.classic_api.get_computer_by_id(1)
    >>> type(computer)
    <class 'jamf_pro_sdk.models.classic.computers.Computer'>
    >>>

The same operation can be performed by using the :meth:`~jamf_pro_sdk.clients.JamfProClient.classic_api_request` method directly:

.. code-block:: python

    >>> response = client.classic_api_request(method='get', resource_path='computers/id/1')
    >>> type(response)
    <class 'requests.models.Response'>

This returns the ``requests.Response`` object unaltered. Note that in the ``resource_path`` argument you do not need to provide `JSSResource`.

Performing Concurrent Operations
--------------------------------

The SDK supports multi-threaded use. The cached access token utilizes a thread lock to prevent multiple threads from refreshing the token if it is expiring. The Jamf Pro client contains a helper method for performing concurrent operations.

Consider the need to perform a mass read operation on computer records. Serially this could take hours for Jamf Pro users with thousands or tens of thousands of devices. With even a concurrency of two the amount of time required can be cut nearly in half.

Here is a code example using :meth:`~jamf_pro_sdk.clients.JamfProClient.concurrent_api_requests` to perform a mass :meth:`~jamf_pro_sdk.clients.classic_api.ClassicApi.get_computer_by_id` operation:

.. code-block:: python

    from jamf_pro_sdk import JamfProClient, ApiClientCredentialsProvider

    # The default concurrency setting is 10.
    client = JamfProClient(
        server="jamf.my.org",
        credentials=ApiClientCredentialsProvider("client_id", "client_secret")
    )

    # Get a list of all computers, and then their IDs.
    all_computers = client.classic_api.list_all_computers()
    all_computer_ids = [c.id for c in all_computers]

    # Pass the API operation and list of IDs into the `concurrent_api_requests()` method.
    results = client.concurrent_api_requests(
        handler=client.classic_api.get_computer_by_id,
        arguments=all_computer_ids
    )

    # Iterate over the results.
    for r in results:
        print(r.general.id, r.general.name, r.location.username)

The ``handler`` is any callable function.

The ``arguments`` can be any iterable. Each item within the iterable is passed to the handler as its argument. If your handler takes multiple arguments you can use a ``dict`` which will be unpacked automatically.

Here is the functional code as above but using the ```~jamf_pro_sdk.clients.JamfProClient.classic_api_request`` method:

.. code-block:: python

    # Construct the arguments by iterating over the computer IDs and creating the argument dictionary
    results = client.concurrent_api_requests(
        handler=client.classic_api_request,
        arguments=[{"method": "get", "resource_path": f"computers/id/{i.id}"} for i in all_computer_ids],
        return_model=Computer
    )

    # Iterate over the results.
    for r in results:
        print(r.general.id, r.general.name, r.location.username)

If you have to perform more complex logic in the threaded operations you can wrap it into another function and pass that. Here is an example that is performing a read following by a conditional update.

.. code-block:: python

    def wrapper(computer_id, new_building):
        current = client.get_computer_by_id(computer_id, subsets=["location"])
        update = Computer()
        if current.location.building in ("Day 1", "Low Flying Hawk"):
            update.location.building = new_building
        else:
            return "Not Updated"

        client.update_computer_by_id(computer_id, )
        return "Updated"

    results = client.concurrent_api_requests(
        wrapper, [{"computer_id": 1, "new_building": ""}]
    )

Performing Async Concurrent Operations
---------------------------------------

The async client provides even more efficient concurrent operations using Python's ``asyncio`` library. The :meth:`~jamf_pro_sdk.clients.AsyncJamfProClient.async_concurrent_api_requests` method works similarly to the synchronous version but leverages async/await for better performance.

Basic Async Concurrent Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is an async version of the mass read operation:

.. code-block:: python

    import asyncio
    from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider

    async def main():
        # The default concurrency setting is 5.
        async with AsyncJamfProClient(
            server="jamf.my.org",
            credentials=ApiClientCredentialsProvider("client_id", "client_secret")
        ) as client:
            # Get a list of all computers, and then their IDs.
            all_computers = await client.classic_api.list_all_computers()
            all_computer_ids = [c.id for c in all_computers]
            
            # Pass the API operation and list of IDs into the async method.
            async for computer in client.async_concurrent_api_requests(
                handler=client.classic_api.get_computer_by_id,
                arguments=all_computer_ids
            ):
                print(computer.general.id, computer.general.name, computer.location.username)

    asyncio.run(main())

Async Operations with Multiple Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Just like the synchronous version, you can pass dictionaries that will be unpacked:

.. code-block:: python

    import asyncio
    from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    from jamf_pro_sdk.models.classic.computers import Computer

    async def main():
        async with AsyncJamfProClient(
            server="jamf.my.org",
            credentials=ApiClientCredentialsProvider("client_id", "client_secret")
        ) as client:
            all_computers = await client.classic_api.list_all_computers()
            
            # Construct the arguments by iterating over the computer IDs
            args = [
                {"method": "get", "resource_path": f"computers/id/{c.id}"}
                for c in all_computers
            ]
            
            results = client.async_concurrent_api_requests(
                handler=client.async_classic_api_request,
                arguments=args
            )
            
            # Iterate over the results
            async for response in results:
                print(f"Status: {response.status_code}")

    asyncio.run(main())

Complex Async Wrapper Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can wrap complex logic into async functions for concurrent execution:

.. code-block:: python

    import asyncio
    from jamf_pro_sdk import AsyncJamfProClient, ApiClientCredentialsProvider
    from jamf_pro_sdk.models.classic.computers import ClassicComputer

    async def update_computer_if_needed(client, computer_id, new_building):
        """Read a computer and conditionally update its building."""
        current = await client.classic_api.get_computer_by_id(
            computer_id,
            subsets=["location"]
        )
        
        update = ClassicComputer()
        if current.location.building in ("Day 1", "Low Flying Hawk"):
            update.location.building = new_building
            await client.classic_api.update_computer_by_id(computer_id, update)
            return "Updated"
        else:
            return "Not Updated"

    async def main():
        async with AsyncJamfProClient(
            server="jamf.my.org",
            credentials=ApiClientCredentialsProvider("client_id", "client_secret")
        ) as client:
            # Create wrapper that includes the client reference
            async def wrapper(computer_id):
                return await update_computer_if_needed(client, computer_id, "Main Building")
            
            computer_ids = [1, 2, 3, 4, 5]
            async for result in client.async_concurrent_api_requests(
                handler=wrapper,
                arguments=computer_ids
            ):
                print(result)

    asyncio.run(main())

Performance Comparison: Sync vs Async
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Async concurrent operations typically provide better performance than thread-based concurrent operations, especially when making many API requests:

**Synchronous (Thread-based):**

- Uses ``ThreadPoolExecutor`` under the hood
- Each thread has overhead for context switching
- Suitable for most use cases
- Works well with any Python code

**Asynchronous:**

- Uses ``asyncio`` event loop
- Lower overhead than threads
- Better performance for I/O-bound operations
- Requires async/await syntax throughout

For most users, the performance difference will be minimal, but async operations can be significantly faster when dealing with hundreds or thousands of concurrent requests.

.. tip::

    Start with the synchronous client for simplicity. Switch to async if you need to integrate with async frameworks or require maximum performance for large-scale concurrent operations.

Custom Async Credentials Providers
-----------------------------------

You can create custom async credentials providers by implementing the async methods:

.. code-block:: python

    import asyncio
    from jamf_pro_sdk.clients.auth import CredentialsProvider
    from jamf_pro_sdk.models.client import AccessToken

    class AsyncDynamoDBProvider(CredentialsProvider):
        def __init__(self, table_name: str):
            self.table_name = table_name
            super().__init__()
        
        async def _request_access_token_async(self) -> AccessToken:
            """Fetch token from DynamoDB asynchronously."""
            # This is a simplified example
            import aioboto3
            
            session = aioboto3.Session()
            async with session.resource("dynamodb") as dynamodb:
                table = await dynamodb.Table(self.table_name)
                response = await table.get_item(Key={"pk": "access-token"})
                item = response["Item"]
                
                return AccessToken(
                    type="user",
                    token=item["token"],
                    expires=item["expires"]
                )

When creating custom async providers, implement the ``_request_access_token_async`` method to provide async token retrieval. The synchronous ``_request_access_token`` method should also be implemented if you want to support both sync and async clients with the same provider.

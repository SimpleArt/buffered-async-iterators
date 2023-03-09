import asyncio
import sys
from typing import Any, TypeVar

if sys.version_info < (3, 9):
    from typing import AsyncIterable, AsyncIterator, Awaitable
else:
    from collections.abc import AsyncIterable, AsyncIterator, Awaitable

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")

# Implementations of `aiter` and `anext` for `python < 3.10`.
if sys.version_info < (3, 10):

    def aiter(iterable: AsyncIterable[T], /) -> AsyncIterator[T]:
        return type(iterable).__aiter__(iterable)

    def anext(iterator: AsyncIterator[T], /) -> Awaitable[T]:
        return type(iterator).__anext__(iterator)

async def _task(
    iterable: AsyncIterable[Any], queue: Any, /
) -> None:
    """Helper task for exhausting the iterable."""
    try:
        async for x in iterable:
            await queue.put((False, x))
    except BaseException as e:
        await queue.put((True, e))
    else:
        await queue.put((None, None))

async def buffered(
    iterable: AsyncIterable[T],
    /,
    n: int = 1,
) -> AsyncIterator[T]:
    """
    Buffers an iterable, allowing iterations to be ran asynchronously
    with the loop that is currently running it.

    Parameters
    ----------
        iterable:
            An asynchronous iterable that is getting buffered.
        n:
            The buffer size, if positive. Otherwise the buffer size is
            infinite.

    Returns
    -------
        buffered_iterator:
            An asynchronous iterator which is buffered.
    """
    if not isinstance(iterable, AsyncIterable):
        raise TypeError("expected async iterable, got " + type(iterable).__name__)
    elif not isinstance(n, int):
        raise TypeError("expected int, got " + type(n).__name__)
    if n == 1:
        iterator = aiter(iterable)
        async for x in iterator:
            try:
                while True:
                    task = asyncio.create_task(anext(iterator))
                    yield x
                    x = await task
            except StopAsyncIteration:
                pass
            except asyncio.CancelledError:
                task.cancel()
                try:
                    await task
                except:
                    pass
                raise
    else:
        queue = asyncio.Queue(n - 1)
        task = asyncio.create_task(_task(iterable, queue))
        try:
            while True:
                is_error, x = await queue.get()
                if is_error:
                    raise x
                elif is_error is None:
                    break
                yield x
        except asyncio.CancelledError:
            task.cancel()
            try:
                await task
            except:
                pass
            raise

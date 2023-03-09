import asyncio
from typing import Any, AsyncIterable, AsyncIterator, Awaitable, TypeVar

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")


def aiter(__iterable: AsyncIterable[T]) -> AsyncIterator[T]:
    return type(__iterable).__aiter__(__iterable)

def anext(__iterator: AsyncIterator[T]) -> Awaitable[T]:
    return type(__iterator).__anext__(__iterator)

async def _task(
    iterable: AsyncIterable[Any], queue: Any
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
    __iterable: AsyncIterable[T],
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
    if not isinstance(__iterable, AsyncIterable):
        raise TypeError("expected async iterable, got " + type(__iterable).__name__)
    elif not isinstance(n, int):
        raise TypeError("expected int, got " + type(n).__name__)
    if n == 1:
        iterator = aiter(__iterable)
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

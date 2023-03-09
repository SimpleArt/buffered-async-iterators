import asyncio
from enum import Enum, auto
from typing import Any, AsyncIterable, AsyncIterator, TypeVar, Union, overload

T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")

class Missing(enum.Enum):
    """An enum for a missing default parameter."""

    DEFAULT = enum.auto()

    def __repr__(self) -> str:
        return "Missing.DEFAULT"


def aiter(__iterable: AsyncIterable[T]) -> AsyncIterator[T]:
    return type(__iterable).__aiter__(__iterable)

@overload
async def anext(__iterator: AsyncIterator[T]) -> T: ...

@overload
async def anext(
    __iterator: AsyncIterator[T1], __default: T2
) -> Union[T1, T2]: ...

async def anext(
    __iterator: AsyncIterator[T1],
    __default: Union[Missing, T2] = Missing.DEFAULT,
) -> Union[T1, T2]:
    if __default is Missing.DEFAULT:
        return await type(__iterator).__anext__(__iterator)
    try:
        return await type(__iterator).__anext__(__iterator)
    except StopAsyncIteration:
        return __default

async def _task(
    iterator: AsyncIterator[Any], queue: Any, stop: object
) -> None:
    """Helper task for exhausting the iterator."""
    async for x in iterator:
        await queue.put(x)
    await queue.put(stop)

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
    iterator = aiter(__iterable)
    if n == 1:
        async for x in iterator:
            try:
                while True:
                    task = asyncio.create_task(anext(iterator))
                    yield x
                    x = await task
            except StopAsyncIteration:
                pass
    else:
        queue = asyncio.Queue(n - 1)
        stop = object()
        asyncio.create_task(_task(iterator, queue, stop))
        while True:
            x = await queue.get()
            if x is stop:
                break
            yield x

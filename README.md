# buffered-async-iterators

Buffers iterables, allowing iterations to be ran asynchronously with the loop that is currently running it.

## Installation

Windows:

```
py -m pip install buffered-async-iterators
```

Unix/MacOS:

```
python3 -m pip install buffered-async-iterators
```

## Imports

```python
from buffered_async_iterators import buffered
```

## Usage

When using asynchronous generators, the generator is only ran between iterations rather than during iterations. This results in untapped potential, potentially doubling the speed or more when running iterations can be done asynchronously with the current iteration.

Syntax:

```python
async for x in async_iterable:
    ...

# Buffers up to 1 iteration ahead.
# Best if the iterable does not run significantly faster than the loop.
async for x in buffered(async_iterable):
    await loop_process(x)

# Buffers arbitrarily far ahead.
# Best if the iterable can run faster than the loop and there are no
# issues with running ahead e.g. no issues with concurrency or memory.
async for x in buffered(async_iterable, 0):
    await loop_process(x)

# Buffers up to n iterations ahead.
# Best if the iterable can run faster than the loop but there are
# issues with running too far ahead e.g. concurrency or memory.
async for x in buffered(async_iterable):
    await loop_process(x)
```

In the following example, the addition of the buffer allows items to be processed twice as fast.

```python
import asyncio
from time import perf_counter

from buffered_async_iterators import buffered

async def countdown(n):
    for i in range(n, 0, -1):
        print("    Starting countdown for", i)
        await asyncio.sleep(1)  # Something slow like an API request.
        print("    Finished countdown for", i)
        yield i

async def main():
    print("Without buffer:")
    start = perf_counter()
    async for i in countdown(5):
        print("        Starting processing for", i)
        await asyncio.sleep(1)  # Something slow like a database query.
        print("        Finished processing for", i)
    stop = perf_counter()
    print("Time:", stop - start, "seconds")
    print()
    print("With buffer:")
    start = perf_counter()
    async for i in buffered(countdown(5)):
        print("        Starting processing for", i)
        await asyncio.sleep(1)  # Something slow like a database query.
        print("        Finished processing for", i)
    stop = perf_counter()
    print("Time:", stop - start, "seconds")

asyncio.run(main())
```

Output:

```
Without buffer:
    Starting countdown for 5
    Finished countdown for 5
        Starting processing for 5
        Finished processing for 5
    Starting countdown for 4
    Finished countdown for 4
        Starting processing for 4
        Finished processing for 4
    Starting countdown for 3
    Finished countdown for 3
        Starting processing for 3
        Finished processing for 3
    Starting countdown for 2
    Finished countdown for 2
        Starting processing for 2
        Finished processing for 2
    Starting countdown for 1
    Finished countdown for 1
        Starting processing for 1
        Finished processing for 1
Time: 10.079117399873212 seconds

With buffer:
    Starting countdown for 5
    Finished countdown for 5
        Starting processing for 5
    Starting countdown for 4
        Finished processing for 5
    Finished countdown for 4
        Starting processing for 4
    Starting countdown for 3
        Finished processing for 4
    Finished countdown for 3
        Starting processing for 3
    Starting countdown for 2
        Finished processing for 3
    Finished countdown for 2
        Starting processing for 2
    Starting countdown for 1
        Finished processing for 2
    Finished countdown for 1
        Starting processing for 1
        Finished processing for 1
Time: 6.040044100023806 seconds
```

There is a clear difference when running the two. Without the buffer, the generator cannot run at the same time as its consumer is processing previous items. With the buffer, the generator can run while items are being processed, which can provide a noticeable speedup.

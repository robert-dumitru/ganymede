import asyncio
from typing import Any, Awaitable
from tqdm import tqdm


async def coro_tqdm_progress(coro: Awaitable, bar: tqdm, target: int, expected_time: float) -> Any:
    """
    Adds a tqdm progress bar to a coroutine.

    Args:
        coro: coroutine to add progress bar to.
        bar: tqdm bar to progress.
        target: target position on tqdm bar.
        expected_time: expected time that coroutine takes.

    Returns:
        Return value of coroutine.
    """
    running = True

    # increments progress bar while other coro is running
    async def progress_bar():
        timestep = 1
        time_elapsed = 0
        initial_n = bar.n
        nonlocal running
        while running:
            await asyncio.sleep(timestep)
            if time_elapsed < expected_time:
                bar.update(timestep * (target - initial_n) / expected_time)
                time_elapsed += timestep
        return

    # wraps main coro
    async def wrap_coro():
        nonlocal running
        try:
            result = await coro
            running = False
            return result
        except Exception as e:
            running = False
            raise e

    results = await asyncio.gather(wrap_coro(), progress_bar())
    return results[0]

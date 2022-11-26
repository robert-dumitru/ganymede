import asyncio
from typing import Any, Awaitable
from tqdm import tqdm


async def coro_tqdm_progress(coro: Awaitable, bar: tqdm, target: int, expected_time: float) -> Any:
    """
    Adds a tqdm progress bar to a coroutine.

    Args:
        coro: coroutine to add progress bar to.
        bar: TQDM bar to progress.
        target: target position on TQDM bar.
        expected_time: expected time that coroutine takes.

    Returns:
        Return value of coroutine.
    """

    finish_flag = False

    async def progress_bar():
        timestep = 1
        time_elapsed = 0
        initial_n = bar.n
        nonlocal finish_flag
        while True:
            if finish_flag:
                break
            await asyncio.sleep(timestep)
            if time_elapsed < expected_time:
                bar.update(timestep * (target - initial_n) / expected_time)
                time_elapsed += timestep
        return

    async def wrap_coro():
        nonlocal finish_flag
        result = await coro
        finish_flag = True
        return result

    results = await asyncio.gather(wrap_coro(), progress_bar())
    return results[0]

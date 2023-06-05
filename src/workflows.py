from dataclasses import dataclass
from typing import Literal
from tqdm import tqdm
from telebot.types import Message
from typing import Any
import os
import asyncio


@dataclass
class Step:
    step_coro: callable
    message: str
    on_success: Literal["continue"] | callable = "continue"
    on_failure: Literal["continue"] | callable = "continue"
    expected_time: float = 30.


async def pbar_wrapper(step: Step, arg: Any, bar: tqdm) -> Any:
    running = True
    target = bar.n + step.expected_time

    # increments progress bar while other coro is running
    async def progress_bar():
        timestep = 1
        time_elapsed = 0
        nonlocal running
        while running:
            await asyncio.sleep(timestep)
            if time_elapsed < step.expected_time:
                bar.update(timestep)
                time_elapsed += timestep
        return

    # wraps main coro
    async def wrap_coro():
        nonlocal running
        try:
            result = await step.step_coro(arg)
            running = False
            return result
        except Exception as e:
            running = False
            raise e

    results = await asyncio.gather(wrap_coro(), progress_bar())
    bar.n = target
    return results[0]


@dataclass
class Pipeline:
    steps: list[Step]

    def __await__(self, message: Message) -> Any:
        total_expected_time = sum(step.expected_time for step in self.steps)
        pbar = tqdm(
            total=total_expected_time,
            desc="Converting: ",
            unit=" %",
            bar_format="{desc}{percentage:3.0f}%|{bar}|{postfix}",
            postfix=self.steps[0].message,
            leave=True,
            token=os.getenv("IPYNB_TG_TOKEN"),
            chat_id=message.chat.id,
        )
        state = message
        for step in self.steps:
            try:
                state = pbar_wrapper(step, state, pbar)
                if step.on_success == "continue":
                    continue
                else:
                    state = await step.on_success(state)  # noqa: E

            except Exception as e:
                if step.on_failure == "continue":
                    continue
                else:
                    state = await step.on_failure(state, e)  # noqa: E

        pbar.close()
        return state

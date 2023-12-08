from temporalio import activity
from temporalio.worker import Worker
from temporalio.client import Client
import os
import asyncio
import uuid

from workflows.conversion import (
    JupyterConversion,
    upload_mongo_file,
    download_mongo_file,
    preprocess_file,
    convert_file,
    cleanup_path,
)


async def main():
    client = await Client.connect(
        os.getenv("TEMPORAL_ADDRESS", "localhost:7233"), namespace="ganymede"
    )

    task_queue = f"ganymede-task-queue-{uuid.uuid4()}"

    @activity.defn(name="get_task_queue")
    def select_task_queue() -> str:
        return task_queue

    run_futures = []

    handle = Worker(
        client,
        task_queue="ganymede-general-task-queue",
        workflows=[JupyterConversion],
        activities=[select_task_queue],
    )
    run_futures.append(handle.run())

    handle = Worker(
        client,
        task_queue=task_queue,
        activities=[
            upload_mongo_file,
            download_mongo_file,
            preprocess_file,
            convert_file,
            cleanup_path,
        ],
    )
    run_futures.append(handle.run())

    await asyncio.gather(*run_futures)


if __name__ == "__main__":
    asyncio.run(main())

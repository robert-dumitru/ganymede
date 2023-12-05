from temporalio import workflow, activity
from pathlib import Path
from pymongo import MongoClient
import asyncio
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, cast
from nbconvert.exporters import PDFExporter, WebPDFExporter
from nbconvert.preprocessors import LatexPreprocessor
from zipfile import ZipFile
from tarfile import TarFile

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


async def heartbeat_every(delay: float, *details: Any) -> None:
    # Heartbeat every so often while not cancelled
    while True:
        await asyncio.sleep(delay)
        print(f"Heartbeating at {datetime.now()}")
        activity.heartbeat(*details)


def auto_heartbeat(fn: F) -> F:
    # We want to ensure that the type hints from the original callable are
    # available via our wrapper, so we use the functools wraps decorator
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        heartbeat_timeout = activity.info().heartbeat_timeout
        heartbeat_task = None
        if heartbeat_timeout:
            # Heartbeat twice as often as the timeout
            heartbeat_task = asyncio.create_task(
                heartbeat_every(heartbeat_timeout.total_seconds() / 2)
            )
        try:
            return await fn(*args, **kwargs)
        finally:
            if heartbeat_task:
                heartbeat_task.cancel()
                # Wait for heartbeat cancellation to complete
                await asyncio.wait([heartbeat_task])

    return cast(F, wrapper)


@activity.defn
async def get_task_queue() -> str:
    """Stub for typing"""
    raise NotImplementedError


def _download_mongo_file(file_id: str, path: str) -> None:
    # TODO: make sure this is correct lol
    client = MongoClient()
    db = client.ganymede
    fs = db.fs
    fs.download_to_stream(file_id, path)


@activity.defn
@auto_heartbeat
async def download_mongo_file(file_id: str) -> Path:
    tmp_path = Path("tmp") / str(uuid.uuid4())
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _download_mongo_file, file_id, tmp_path)
    return tmp_path


def _upload_mongo_file(path: str) -> str:
    client = MongoClient()
    db = client.ganymede
    fs = db.fs
    new_id = fs.upload_from_stream(path)
    return new_id


@activity.defn
@auto_heartbeat
async def upload_mongo_file(path: str) -> str:
    loop = asyncio.get_running_loop()
    new_id = await loop.run_in_executor(None, _upload_mongo_file, path)
    return new_id


def search_for_notebook(path: Path) -> Path:
    """
    Searches a directory for a jupyter notebook.
    Args:
        path: Path of the directory to search.

    Returns:
        Path of the jupyter notebook.
    """

    def _search(path: Path) -> list[Path]:
        if path.is_dir():
            notebooks = []
            for file in path.iterdir():
                if file.suffix == ".ipynb":
                    notebooks.append(file)
                elif file.is_dir():
                    notebooks.append(_search(file))
            return notebooks
        elif path.suffix == ".ipynb":
            return [path]
        else:
            raise ValueError("Path must be a directory or a jupyter notebook")

    paths = _search(path)
    if len(paths) == 0:
        raise ValueError("No jupyter notebooks found")
    elif len(paths) == 1:
        return paths[0]
    else:
        raise ValueError("Multiple jupyter notebooks found")


def _preprocess_file(path: Path) -> Path:
    match path.suffix:
        case ".ipynb":
            return path
        case ".zip":
            with ZipFile(path, "r") as zip_file:
                zip_file.extractall(path.parent)
            path.unlink()
        case ".tar":
            with TarFile(path, "r") as tar_file:
                tar_file.extractall(path.parent)
            path.unlink()
        case _:
            raise ValueError("File must be a .ipynb, .zip, or .tar")

    notebook_path = search_for_notebook(path)
    return notebook_path


@activity.defn
@auto_heartbeat
async def preprocess_file(path: str) -> str:
    raise NotImplementedError


def _convert_file(path: Path, ctx: dict) -> Path:
    match ctx.get("mode"):
        case "latex":
            exporter = PDFExporter()
            exporter.register_preprocessor(LatexPreprocessor())
            # exporter.template_file = "article.tplx"
        case "webpdf":
            exporter = WebPDFExporter()
        case _:
            raise ValueError("Invalid conversion mode")
    pdf_data, resources = exporter.from_filename(str(path))
    pdf_path = path.with_suffix(".pdf")
    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(pdf_data)  # noqa
    return pdf_path


@activity.defn
@auto_heartbeat
async def convert_file(path: str, opt: dict) -> str:
    raise NotImplementedError


@workflow.defn
class JupyterConversion:
    @workflow.run
    async def run(self, file_id: str, ctx: dict) -> str:
        # assign to worker for file persistence
        task_queue = await workflow.execute_activity(get_task_queue)
        workflow.logger.info(f"Assigned to task queue: {task_queue}")

        # download and preprocess files
        file_path = await workflow.execute_activity(
            download_mongo_file, file_id, task_queue=task_queue
        )
        await workflow.execute_activity(
            preprocess_file, file_path, task_queue=task_queue
        )

        # sentinel value for invalid conversions
        output_path = None
        # loop through conversion modes specified in ctx
        for mode in ctx.get("mode_sequence", ["latex", "webpdf"]):
            try:
                output_path = await workflow.execute_activity(
                    convert_file, file_path, {"mode": mode}, task_queue=task_queue
                )
            except Exception as e:
                workflow.logger.error(f"Error converting file to {mode}: {e}")
        # if no valid conversion modes succeeded, raise error
        if not output_path:
            raise ValueError("No valid conversion modes succeeded")
        # otherwise, upload converted file to mongo
        new_file_id = await workflow.execute_activity(
            upload_mongo_file, file_path, task_queue=task_queue
        )
        return new_file_id

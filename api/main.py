from fastapi import FastAPI, BackgroundTasks
from typing import Literal
from pydantic import BaseModel
from datetime import datetime
import asyncpg
import os

app = FastAPI()


class JobRequest(BaseModel):
    file_id: str


class JobStatus(BaseModel):
    id: str
    status: Literal["running", "success", "error"]
    start_time: datetime
    error: str | None = None
    input_file_id: str | None = None


async def download_file(file_id: str) -> tuple[str | None, NotImplementedError | None]:
    return None, NotImplementedError()


async def convert_webpdf(path: str) -> tuple[str | None, NotImplementedError | None]:
    return None, NotImplementedError()


async def convert_latex(path: str) -> tuple[str | None, NotImplementedError | None]:
    return None, NotImplementedError()


async def convert(job: JobStatus) -> None:
    pass


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@app.post("/convert", status_code=202)
async def start_job(
    job_request: JobRequest, background_tasks: BackgroundTasks
) -> JobStatus:
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    job_row = await conn.fetchrow(
        """
            INSERT INTO jobs (input_file_id) VALUES ($1) RETURNING *;
        """,
        job_request.file_id,
    )

    if job_row is None:
        raise Exception("Cannot create job")

    job_status = JobStatus(**dict(job_row))  # pyright: ignore[reportAny]
    background_tasks.add_task(convert, job_status)
    return job_status


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    job_row = await conn.fetchrow(
        """
            SELECT * FROM jobs WHERE id = $1;
        """,
        job_id,
    )

    if job_row is None:
        raise Exception("Cannot create job")

    job_status = JobStatus(**dict(job_row))  # pyright: ignore[reportAny]
    return job_status

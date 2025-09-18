from fastapi import FastAPI, BackgroundTasks
from typing import Literal
from pydantic import BaseModel
from datetime import datetime, timezone
import asyncpg
import os
from contextlib import asynccontextmanager

db_pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # pyright: ignore[reportUnusedParameter]
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=os.getenv("DATABASE_URL"))
    yield
    await db_pool.close()


app = FastAPI()


class JobRequest(BaseModel):
    file_id: str


class JobStatus(BaseModel):
    id: str
    input_file_id: str
    status: Literal["running", "success", "error"]
    started_at: datetime
    error: str | None = None
    output_file_id: str | None = None


async def download_file(file_id: str) -> str:
    raise NotImplementedError


async def upload_file(path: str) -> str:
    raise NotImplementedError


async def convert_webpdf(path: str) -> str:
    raise NotImplementedError


async def convert_latex(path: str) -> str:
    raise NotImplementedError


async def record_error(job_id: str, error: str) -> None:
    if db_pool is None:
        raise Exception("DB Pool is not initialized")

    async with db_pool.acquire() as conn:
        _ = await conn.execute(
            """
                UPDATE jobs SET status='error', error=$1, finished_at=$2 WHERE id=$3
            """,
            error,
            datetime.now(timezone.utc),
            job_id,
        )


async def record_success(job_id: str, output_file_id: str) -> None:
    if db_pool is None:
        raise Exception("DB Pool is not initialized")

    async with db_pool.acquire() as conn:
        _ = await conn.execute(
            """
                UPDATE jobs SET status='success', output_file_id=$1, finished_at=$2 WHERE id=$3
            """,
            output_file_id,
            datetime.now(timezone.utc),
            job_id,
        )


async def convert(job: JobStatus) -> None:
    pass


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@app.post("/convert", status_code=202)
async def start_job(
    job_request: JobRequest, background_tasks: BackgroundTasks
) -> JobStatus:
    if db_pool is None:
        raise Exception("DB Pool is not initialized")

    async with db_pool.acquire() as conn:
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
    if db_pool is None:
        raise Exception("DB Pool is not initialized")
    async with db_pool.acquire() as conn:
        job_row = await conn.fetchrow(
            """
                SELECT * FROM jobs WHERE id = $1;
            """,
            job_id,
        )

    if job_row is None:
        raise Exception("No job found")

    job_status = JobStatus(**dict(job_row))  # pyright: ignore[reportAny]
    return job_status

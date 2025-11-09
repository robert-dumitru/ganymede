from fastapi import FastAPI, BackgroundTasks, HTTPException
from typing import Literal
from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID
import os
from contextlib import asynccontextmanager
from pathlib import Path
import shutil

from .database import db
from .conversions import download_file, upload_file, prepare_files, convert_latex, convert_webpdf


@asynccontextmanager
async def lifespan(app: FastAPI):  # pyright: ignore[reportUnusedParameter]
    await db.connect(os.getenv("DATABASE_URL"))
    yield
    await db.close()


app = FastAPI(lifespan=lifespan)


class JobRequest(BaseModel):
    file_id: str


class JobStatus(BaseModel):
    id: str
    input_file_id: str
    status: Literal["running", "success", "error"]
    started_at: datetime
    error: str | None = None
    output_file_id: str | None = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


async def convert(job: JobStatus) -> None:
    """
    Main conversion orchestration: download, prepare, convert (LaTeX then WebPDF fallback), upload.

    This function handles all errors and updates the job status accordingly.
    """
    local_path: str | None = None

    try:
        # 1. Download file from S3
        local_path = await download_file(job.input_file_id)

        # 2. Prepare files (validate and extract if needed)
        ipynb_path = await prepare_files(local_path)

        # 3. Try LaTeX conversion first, fallback to WebPDF
        try:
            pdf_path = await convert_latex(ipynb_path)
        except Exception:
            # Fallback to WebPDF if LaTeX failed
            pdf_path = await convert_webpdf(ipynb_path)

        # 4. Upload result to S3
        output_id = await upload_file(pdf_path)

        # 5. Record success
        await db.record_success(job.id, output_id)

    except Exception as e:
        # Record any error that occurred
        await db.record_error(job.id, str(e))

    finally:
        # 6. Cleanup temporary files
        if local_path:
            try:
                # Clean up the job directory
                job_dir = Path(local_path).parent
                if job_dir.exists() and "ganymede-" in str(job_dir):
                    shutil.rmtree(job_dir, ignore_errors=True)
            except Exception:
                # Best effort cleanup, don't fail the job if cleanup fails
                pass


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}


@app.post("/convert", status_code=202)
async def start_job(
    job_request: JobRequest, background_tasks: BackgroundTasks
) -> JobStatus:
    job_status = await db.create_job(job_request.file_id)
    background_tasks.add_task(convert, job_status)
    return job_status


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> JobStatus:
    job_status = await db.get_job(job_id)
    if job_status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_status

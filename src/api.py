from fastapi import FastAPI, UploadFile, File
from typing import Literal, Optional
from pydantic import BaseModel
from datetime import datetime
app = FastAPI()

class JobRequest(BaseModel):
    file_id: str
    mode: Literal["latex", "webpdf"]

class JobStatus(BaseModel):
    status: Literal["pending", "running", "completed", "failed"]
    start_time: datetime
    error: Optional[str] = None
    file_id: Optional[str] = None

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}

@app.post("/convert")
async def jupyter(job_request: JobRequest):
    return {"status": "ok"}


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    return {"status": "ok"}
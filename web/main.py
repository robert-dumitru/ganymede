import os
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aiofiles
import aioboto3
import httpx

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

# Setup FastAPI app
app = FastAPI(title="Ganymede Web UI")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


async def upload_to_s3(file_content: bytes, filename: str) -> str:
    """Upload file to S3 and return file_id"""
    if not all([S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        raise HTTPException(status_code=500, detail="S3 configuration incomplete")

    # Generate unique file ID
    file_id = f"uploads/{uuid.uuid4()}/{filename}"

    try:
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
        ) as s3:
            await s3.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=file_id,
                Body=file_content,
            )
        return file_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")


async def download_from_s3(file_id: str) -> bytes:
    """Download file from S3"""
    if not all([S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        raise HTTPException(status_code=500, detail="S3 configuration incomplete")

    try:
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
        ) as s3:
            response = await s3.get_object(Bucket=S3_BUCKET_NAME, Key=file_id)
            async with response["Body"] as stream:
                return await stream.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 download failed: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve main upload page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Handle file upload, upload to S3, and submit to API"""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(('.ipynb', '.zip')):
        return """
        <div id="status" class="error">
            <span class="status-label">Error</span>
            <p>Only .ipynb and .zip files are allowed</p>
        </div>
        """

    # Read file content
    file_content = await file.read()

    # Check file size
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return f"""
        <div id="status" class="error">
            <span class="status-label">Error</span>
            <p>File size ({file_size_mb:.2f}MB) exceeds limit ({MAX_FILE_SIZE_MB}MB)</p>
        </div>
        """

    try:
        # Upload to S3
        file_id = await upload_to_s3(file_content, file.filename)

        # Submit job to API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/convert",
                json={"file_id": file_id},
                timeout=10.0
            )
            response.raise_for_status()
            job = response.json()

        # Return status fragment that will poll for updates
        return f"""
        <div id="status" hx-get="/status/{job['id']}" hx-trigger="load delay:2s" hx-swap="outerHTML">
            <span class="status-label">Job Status</span>
            <p>Job ID: {job['id'][:8]}...</p>
            <p>Status: {job['status']}</p>
            <p class="spinner">
                <span class="spinner-text">Converting...</span>
            </p>
        </div>
        """
    except httpx.HTTPError as e:
        return f"""
        <div id="status" class="error">
            <span class="status-label">Error</span>
            <p>API request failed: {str(e)}</p>
        </div>
        """
    except Exception as e:
        return f"""
        <div id="status" class="error">
            <span class="status-label">Error</span>
            <p>{str(e)}</p>
        </div>
        """


@app.get("/status/{job_id}", response_class=HTMLResponse)
async def get_status(job_id: str):
    """Poll API for job status and return status fragment"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/jobs/{job_id}", timeout=10.0)
            response.raise_for_status()
            job = response.json()

        status = job["status"]

        if status == "running":
            # Still running, continue polling
            return f"""
            <div id="status" hx-get="/status/{job_id}" hx-trigger="load delay:2s" hx-swap="outerHTML">
                <span class="status-label">Job Status</span>
                <p>Job ID: {job_id[:8]}...</p>
                <p>Status: {status}</p>
                <p class="spinner">
                    <span class="spinner-text">Converting...</span>
                </p>
            </div>
            """
        elif status == "success":
            # Conversion complete
            output_file_id = job.get("output_file_id", "")
            return f"""
            <div id="status" class="success">
                <span class="status-label">Conversion Complete</span>
                <p>Job ID: {job_id[:8]}...</p>
                <p>Your PDF is ready for download.</p>
                <p class="status-action">
                    <a href="/download/{output_file_id}" class="download-link">Download PDF</a>
                </p>
                <p class="status-secondary-action">
                    <a href="/">Convert Another File</a>
                </p>
            </div>
            """
        else:  # error
            error_msg = job.get("error", "Unknown error")
            return f"""
            <div id="status" class="error">
                <span class="status-label">Conversion Failed</span>
                <p>Job ID: {job_id[:8]}...</p>
                <p>Error: {error_msg}</p>
                <p class="status-secondary-action">
                    <a href="/">Try Again</a>
                </p>
            </div>
            """
    except httpx.HTTPError as e:
        return f"""
        <div id="status" class="error">
            <span class="status-label">Error</span>
            <p>Failed to check job status: {str(e)}</p>
        </div>
        """
    except Exception as e:
        return f"""
        <div id="status" class="error">
            <span class="status-label">Error</span>
            <p>{str(e)}</p>
        </div>
        """


@app.get("/download/{file_id:path}")
async def download_file(file_id: str):
    """Proxy download from S3"""
    try:
        file_content = await download_from_s3(file_id)

        # Extract filename from file_id or use default
        filename = file_id.split("/")[-1] if "/" in file_id else "output.pdf"

        return StreamingResponse(
            iter([file_content]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

import os
import uuid
import asyncio
import aiofiles
import aioboto3
import zipfile
import json
import shutil
from pathlib import Path
from nbconvert import PDFExporter, WebPDFExporter


# Configuration - imported from environment
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
LATEX_TIMEOUT_SEC = int(os.getenv("LATEX_TIMEOUT_SEC", "120"))
WEBPDF_TIMEOUT_SEC = int(os.getenv("WEBPDF_TIMEOUT_SEC", "180"))
WORKDIR = os.getenv("WORKDIR", "/tmp")


# Custom exceptions
class StorageError(Exception):
    """S3/storage operation failed"""
    pass


class ConversionError(Exception):
    """PDF conversion operation failed"""
    pass


async def download_file(file_id: str) -> str:
    """
    Downloads file from S3-compatible storage and returns a local path.

    Raises:
        StorageError: If S3 configuration is incomplete or download fails
        ValueError: If file size exceeds limit
    """
    if not all([S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        raise StorageError("S3 configuration is incomplete")

    # Create temporary directory for this job
    job_dir = Path(WORKDIR) / f"ganymede-{uuid.uuid4()}"
    job_dir.mkdir(parents=True, exist_ok=True)

    # Determine local path based on file_id
    local_path = job_dir / file_id.split("/")[-1]

    try:
        # Download from S3
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
        ) as s3:
            # Check file size before downloading
            head_response = await s3.head_object(Bucket=S3_BUCKET_NAME, Key=file_id)
            file_size_mb = head_response["ContentLength"] / (1024 * 1024)

            if file_size_mb > MAX_FILE_SIZE_MB:
                shutil.rmtree(job_dir, ignore_errors=True)
                raise ValueError(f"File size ({file_size_mb:.2f}MB) exceeds limit ({MAX_FILE_SIZE_MB}MB)")

            # Download file
            async with aiofiles.open(local_path, "wb") as f:
                response = await s3.get_object(Bucket=S3_BUCKET_NAME, Key=file_id)
                async with response["Body"] as stream:
                    while chunk := await stream.read(8192):
                        await f.write(chunk)

        return str(local_path)
    except ValueError:
        raise  # Re-raise file size errors
    except Exception as e:
        raise StorageError(f"Failed to download file {file_id}") from e


async def upload_file(path: str) -> str:
    """
    Uploads file to S3-compatible storage and returns file_id.

    Raises:
        StorageError: If S3 configuration is incomplete or upload fails
    """
    if not all([S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET_NAME]):
        raise StorageError("S3 configuration is incomplete")

    # Generate unique file ID
    file_id = f"outputs/{uuid.uuid4()}.pdf"

    try:
        # Upload to S3
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
        ) as s3:
            async with aiofiles.open(path, "rb") as f:
                content = await f.read()
                await s3.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=file_id,
                    Body=content,
                    ContentType="application/pdf",
                )

        return file_id
    except Exception as e:
        raise StorageError(f"Failed to upload file") from e


async def prepare_files(path: str) -> str:
    """
    Prepares the downloaded file. If it's a .ipynb, validates it.
    If it's a .zip, extracts and validates.

    Returns: Path to validated .ipynb file

    Raises:
        ValueError: If file type is invalid or validation fails
    """
    file_path = Path(path)

    # Validate file type
    if not file_path.suffix.lower() in [".ipynb", ".zip"]:
        raise ValueError(f"Invalid file type: {file_path.suffix}. Only .ipynb and .zip are allowed")

    # Handle .ipynb files
    if file_path.suffix.lower() == ".ipynb":
        # Validate JSON structure
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                notebook = json.loads(content)

            # Basic validation: check if it has required notebook structure
            if "cells" not in notebook or "metadata" not in notebook:
                raise ValueError("Invalid notebook structure: missing 'cells' or 'metadata'")

            return str(file_path)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in notebook: {e}") from e

    # Handle .zip files
    elif file_path.suffix.lower() == ".zip":
        extract_dir = file_path.parent / f"extracted-{uuid.uuid4()}"
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Extract zip with path traversal protection
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                ipynb_files = []

                for member in zip_ref.namelist():
                    # Security: Check for path traversal attempts
                    member_path = Path(member)
                    if member_path.is_absolute() or ".." in member_path.parts:
                        raise ValueError(f"Invalid path in zip: {member}")

                    # Extract only .ipynb files
                    if member.lower().endswith(".ipynb"):
                        # Extract safely
                        zip_ref.extract(member, extract_dir)
                        ipynb_files.append(extract_dir / member)

                # Validate exactly one .ipynb file
                if len(ipynb_files) == 0:
                    raise ValueError("Zip file must contain at least one .ipynb file")
                if len(ipynb_files) > 1:
                    raise ValueError(f"Zip file must contain exactly one .ipynb file, found {len(ipynb_files)}")

                ipynb_path = ipynb_files[0]

                # Validate the extracted notebook
                async with aiofiles.open(ipynb_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    notebook = json.loads(content)

                if "cells" not in notebook or "metadata" not in notebook:
                    raise ValueError("Invalid notebook structure in zip")

                return str(ipynb_path)

        except zipfile.BadZipFile as e:
            raise ValueError("Invalid or corrupted zip file") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in extracted notebook: {e}") from e


async def convert_latex(path: str) -> str:
    """
    Runs nbconvert in LaTeX mode, returns path to generated PDF.

    Raises:
        TimeoutError: If conversion exceeds timeout
        ConversionError: If conversion fails
    """
    file_path = Path(path)

    # Configure PDF exporter with LaTeX backend
    exporter = PDFExporter()
    # SECURITY: Disable code execution
    exporter.exclude_input_prompt = False
    if hasattr(exporter, "execute_preprocessor"):
        exporter.execute_preprocessor.enabled = False

    try:
        # Run conversion with timeout
        async def _convert():
            # Run in executor since nbconvert is sync
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, exporter.from_filename, str(file_path))

        body, resources = await asyncio.wait_for(_convert(), timeout=LATEX_TIMEOUT_SEC)

        # Save PDF to file
        output_path = file_path.parent / f"{file_path.stem}.pdf"
        async with aiofiles.open(output_path, "wb") as f:
            await f.write(body)

        return str(output_path)

    except asyncio.TimeoutError:
        raise TimeoutError(f"LaTeX conversion timed out after {LATEX_TIMEOUT_SEC} seconds")
    except Exception as e:
        raise ConversionError(f"LaTeX conversion failed") from e


async def convert_webpdf(path: str) -> str:
    """
    Runs nbconvert in WebPDF mode, returns path to generated PDF.

    Raises:
        TimeoutError: If conversion exceeds timeout
        ConversionError: If conversion fails
    """
    file_path = Path(path)

    # Configure WebPDF exporter
    exporter = WebPDFExporter()
    # SECURITY: Disable code execution
    if hasattr(exporter, "execute_preprocessor"):
        exporter.execute_preprocessor.enabled = False

    # SECURITY: Keep Chromium sandbox enabled (user specified this)
    # Note: This may require proper security context in K8s
    if hasattr(exporter, "disable_sandbox"):
        exporter.disable_sandbox = False

    try:
        # Run conversion with timeout
        async def _convert():
            # Run in executor since nbconvert is sync
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, exporter.from_filename, str(file_path))

        body, resources = await asyncio.wait_for(_convert(), timeout=WEBPDF_TIMEOUT_SEC)

        # Save PDF to file
        output_path = file_path.parent / f"{file_path.stem}.pdf"
        async with aiofiles.open(output_path, "wb") as f:
            await f.write(body)

        return str(output_path)

    except asyncio.TimeoutError:
        raise TimeoutError(f"WebPDF conversion timed out after {WEBPDF_TIMEOUT_SEC} seconds")
    except Exception as e:
        raise ConversionError(f"WebPDF conversion failed") from e

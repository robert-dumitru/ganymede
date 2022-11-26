import asyncio
import logging
import os

# TODO: call python functions instead?


async def latex_convert(ipynb_path: str, workdir: str) -> str:
    """
    Converts the ipynb file into a pdf using latex.

    Args:
        ipynb_path: path to the ipynb file.
        workdir: path to the working directory.

    Returns: path of pdf.
    """
    proc = await asyncio.create_subprocess_exec(
        "jupyter",
        "nbconvert",
        "--to",
        "pdf",
        ipynb_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workdir,
    )
    logging.debug(f"Completed process: {proc}")
    if proc.returncode != 0:
        stdout, stderr = await proc.communicate()
        logging.warning(f"STDOUT: {stdout}")
        logging.error(f"STDERR: {stderr}")
        raise SystemError(f"Failed to convert notebook via LaTeX")
    pdf_path = os.path.splitext(ipynb_path)[0] + ".pdf"
    return pdf_path


async def chromium_convert(ipynb_path: str, workdir: str) -> str:
    """
    Converts the ipynb file into a pdf using chromium and pyppeteer.

    Args:
        ipynb_path: path to the ipynb file.
        workdir: path to the working directory.

    Returns: path of pdf.
    """
    proc = await asyncio.create_subprocess_exec(
        "jupyter",
        "nbconvert",
        ipynb_path,
        "--to",
        "webpdf",
        "--disable-chromium-sandbox",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=workdir,
    )
    logging.debug(f"Completed process: {proc}")
    if proc.returncode != 0:
        stdout, stderr = await proc.communicate()
        logging.warning(f"STDOUT: {stdout}")
        logging.error(f"STDERR: {stderr}")
        raise SystemError(f"Failed to convert notebook via Chromium")
    pdf_path: str = os.path.splitext(ipynb_path)[0] + ".pdf"
    return pdf_path

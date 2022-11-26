import logging
import os
import asyncio
import aiofiles
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Document


async def load_files(tb: AsyncTeleBot, document: Document, workdir: str) -> str:
    """
    Loads the files from the Telegram message into the local filesystem and checks structure.

    Args:
        tb: TeleBot instance.
        document: Telegram document object.
        workdir: path to the working directory.

    Returns: None
    """
    proc = await asyncio.create_subprocess_exec(
        "mkdir",
        "-p",
        workdir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    if proc.returncode != 0:
        stdout, stderr = await proc.communicate()
        logging.warning(f"STDOUT: {stdout}")
        logging.error(f"STDERR: {stderr}")
        raise SystemError(f"Unable to create directory {workdir}")
    file_info = await tb.get_file(document.file_id)
    file_bytes = await tb.download_file(file_info.file_path)
    async with aiofiles.open(f"{workdir}/{document.file_name}", "wb") as file:
        await file.write(file_bytes)
    logging.debug(f"Downloaded file to {workdir}/{document.file_name}")
    file_body, ext = os.path.splitext(document.file_name)
    match ext:
        case ".ipynb":
            return document.file_name
        case ".zip":
            proc = await asyncio.create_subprocess_exec(
                "unzip",
                f"{workdir}/{document.file_name}",
                "-d",
                workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            if proc.returncode != 0:
                stdout, stderr = await proc.communicate()
                logging.warning(f"STDOUT: {stdout}")
                logging.error(f"STDERR: {stderr}")
                raise SystemError(f"Unable to unzip {workdir}/{document.file_name}")
            ipynb_files = [
                file
                for file in os.listdir(workdir)
                if os.path.splitext(file)[1] == ".ipynb"
            ]
            if len(ipynb_files) == 0:
                raise TypeError(f"No ipynb file found: {os.listdir(workdir)}")
            elif len(ipynb_files) > 1:
                raise TypeError(f"Too many ipynb files found: {os.listdir(workdir)}")
            else:
                return ipynb_files[0]
        case _:
            raise TypeError(f"Wrong file type: {ext}")


async def cleanup_files(workdir: str) -> None:
    """
    Removes the files from the local filesystem.

    Args:
        workdir: path to the working directory.

    Returns: None
    """
    proc = await asyncio.create_subprocess_exec(
        "rm",
        "-rf",
        workdir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    if proc.returncode != 0:
        stdout, stderr = await proc.communicate()
        logging.warning(f"STDOUT: {stdout}")
        logging.error(f"STDERR: {stderr}")
        raise SystemError(f"Failed to remove folder: {workdir}")
    logging.debug(f"Removed {workdir}")
    return

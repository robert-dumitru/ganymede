import subprocess
import os
import logging
import telebot

from exceptions import WrongTypeFileError, NoNBFileError, TooManyNBsFileError


def load_files(tb: telebot.TeleBot, document: telebot.types.Document, workdir: str = "/tmp") -> None:
    """
    Loads the files from the Telegram message into the local filesystem.

    Args:
        tb: Telebot instance.
        document: Telegram document object.
        workdir: path to load files into.

    Returns: None
    """
    # clear any remnants from previous runs (in case instance is already spun up)
    subprocess.call(f"rm -rf {workdir}/", shell=True)
    file_url: str = tb.get_file_url(document.file_id)
    with open(f"{workdir}/file", "wb") as file:
        file.write(tb.download_file(file_url))
    logging.debug(f"Downloaded file to {workdir}/{document.file_name}")
    file_body: str
    ext: str
    file_body, ext = os.path.splitext(document.file_name)
    if ext == "ipynb":
        # if we get an ipynb file, we can render it without modifications
        return
    elif ext == "zip":
        subprocess.run(["unzip", f"{workdir}/{document.file_name}", "-d", f"{workdir}"])
    else:
        raise WrongTypeFileError(f"Wrong file type: {ext}")


def check_files(workdir: str = "/tmp") -> str:
    """
    Checks files to ensure they are valid, then returns the path to the master ipynb file.

    Args:
        workdir: path to check files in.

    Returns:
        str: path to the master notebook file.
    """
    # Separate out ipynb files
    ipynb_files = [file for file in os.listdir(workdir) if os.path.splitext(file)[1] == ".ipynb"]
    if len(ipynb_files) == 0:
        raise NoNBFileError(f"No ipynb file found: {os.listdir(workdir)}")
    elif len(ipynb_files) > 1:
        raise TooManyNBsFileError(f"Too many ipynb files found: {ipynb_files}")
    # return the master ipynb file
    else:
        return ipynb_files[0]




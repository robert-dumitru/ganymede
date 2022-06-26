import subprocess
import os
import logging
# noinspection PyPackageRequirements
import telebot

from exceptions import WrongTypeFileError, NoNBFileError, TooManyNBsFileError


def load_files(tb: telebot.TeleBot, document: telebot.types.Document, path: str = "/tmp") -> None:
    """
    Loads the files from the Telegram message into the local filesystem.

    Args:
        tb: telebot instance.
        document: Telegram document object.
        path: path to load files into.

    Returns: None
    """
    # clear any remnants from previous runs (in case instance is already spun up)
    subprocess.call(f"rm -rf {path}/", shell=True)
    file_url: str = tb.get_file_url(document.file_id)
    with open(f"{path}/file", "wb") as file:
        file.write(tb.download_file(file_url))
    logging.debug(f"Downloaded file to {path}/{document.file_name}")
    file_body: str
    ext: str
    file_body, ext = os.path.splitext(document.file_name)
    if ext == "ipynb":
        # if we get an ipynb file, we can render it without modifications
        return
    elif ext == "zip":
        subprocess.run(["unzip", f"{path}/{document.file_name}", "-d", f"{path}"])
    else:
        raise WrongTypeFileError(f"Wrong file type: {ext}")


def check_files(path: str = "/tmp") -> str:
    """
    Checks files to ensure they are valid, then returns the path to the master ipynb file.

    Args:
        path: path to check files in.

    Returns:
        str: path to the master notebook file.
    """
    # Separate out ipynb files
    ipynb_files = [file for file in os.listdir(path) if os.path.splitext(file)[1] == ".ipynb"]
    if len(ipynb_files) == 0:
        raise NoNBFileError(f"No ipynb file found: {os.listdir(path)}")
    elif len(ipynb_files) > 1:
        raise TooManyNBsFileError(f"Too many ipynb files found: {ipynb_files}")
    # return the master ipynb file
    else:
        return ipynb_files[0]




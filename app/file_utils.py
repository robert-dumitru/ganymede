import subprocess
import os
import logging
import telebot


def load_files(tb: telebot.TeleBot, document: telebot.types.Document, workdir: str = "/tmp") -> str:
    """
    Loads the files from the Telegram message into the local filesystem and checks structure.

    Args:
        tb: Telebot instance.
        document: Telegram document object.
        workdir: path to load files into.

    Returns: None
    """
    # clear any remnants from previous runs (in case instance is already spun up)
    subprocess.call(f"rm -rf {workdir}/*", shell=True)
    file_info: telebot.types.File = tb.get_file(document.file_id)
    with open(f"{workdir}/{document.file_name}", "wb") as file:
        file.write(tb.download_file(file_info.file_path))
    logging.debug(f"Downloaded file to {workdir}/{document.file_name}")
    file_body: str
    ext: str
    file_body, ext = os.path.splitext(document.file_name)
    if ext == ".ipynb":
        # if we get an ipynb file, we can render it without modifications
        pass
    elif ext == ".zip":
        # zip files need to be unzipped
        subprocess.run(["unzip", f"{workdir}/{document.file_name}", "-d", f"{workdir}"])
    else:
        raise TypeError(f"Wrong file type: {ext}")
    ipynb_files = [file for file in os.listdir(workdir) if os.path.splitext(file)[1] == ".ipynb"]
    # check file structure
    if len(ipynb_files) == 0:
        raise TypeError(f"No ipynb file found: {os.listdir(workdir)}")
    elif len(ipynb_files) > 1:
        raise TypeError(f"Too many ipynb files found: {os.listdir(workdir)}")
    # return the master ipynb file
    else:
        return ipynb_files[0]



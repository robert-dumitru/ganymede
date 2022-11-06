import telebot
import subprocess
import logging
import os


def load_files(tb: telebot.TeleBot, document: telebot.types.Document, workdir: str) -> str:
    """
    Loads the files from the Telegram message into the local filesystem and checks structure.

    Args:
        tb: TeleBot instance.
        document: Telegram document object.
        workdir: path to the working directory.

    Returns: None
    """
    root_path: str = os.environ["ROOT_PATH"]
    # clear any remnants from previous runs (in case instance is already spun up)
    subprocess.run(["mkdir", "-p", workdir], cwd=root_path)
    path: str = root_path + workdir
    file_info: telebot.types.File = tb.get_file(document.file_id)
    with open(f"{path}/{document.file_name}", "wb") as file:
        file.write(tb.download_file(file_info.file_path))
    logging.debug(f"Downloaded file to {path}/{document.file_name}")
    file_body: str
    ext: str
    file_body, ext = os.path.splitext(document.file_name)
    if ext == ".ipynb":
        # if we get an ipynb file, we can render it without modifications
        pass
    elif ext == ".zip":
        # zip files need to be unzipped
        subprocess.run(["unzip", document.file_name, "-d", "."], cwd=path)
    else:
        raise TypeError(f"Wrong file type: {ext}")
    ipynb_files = [file for file in os.listdir(path) if os.path.splitext(file)[1] == ".ipynb"]
    # check file structure
    if len(ipynb_files) == 0:
        raise TypeError(f"No ipynb file found: {os.listdir(path)}")
    elif len(ipynb_files) > 1:
        raise TypeError(f"Too many ipynb files found: {os.listdir(path)}")
    # return the master ipynb file
    else:
        return ipynb_files[0]


def cleanup_files(workdir: str) -> None:
    """
    Removes the files from the local filesystem.

    Args:
        workdir: path to the working directory.

    Returns: None
    """
    root_path: str = os.environ["ROOT_PATH"]
    subprocess.run(["rm", "-rf", workdir], cwd=root_path)
    logging.debug(f"Removed {workdir} from {root_path}")
    return

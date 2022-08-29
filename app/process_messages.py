"""
If you're reading this, you've reached the guts of this bot. There are a ton of kludges here, and I'm not proud of it.
For example, all of these functions need to be in the same file for both ec2 and lambda to work. If you want to
contribute, this is the place that most sorely needs it.
"""

import os
import json
import logging
import uuid
import time
import subprocess
from concurrent.futures import ProcessPoolExecutor, Future
from typing import Any
import telebot
from tqdm.contrib.telegram import tqdm

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
telebot.logger.setLevel(logging.DEBUG)
# make sure to set the environment variable to bot token
tb: telebot.TeleBot = telebot.TeleBot(os.environ["TELEGRAM_TOKEN"], threaded=False)

ROOT_PATH: str = "/home/ubuntu/ipynbconverterbot/tmp/"


def handler(event: dict, context: dict) -> None:
    """
    This function handles messages from the user and directs them to the appropriate conversion function.

    Args:
        event: AWS Gateway event.
        context: Lambda Context.

    Returns: None.
    """
    logging.debug(f"Received event: {event}")
    logging.debug(f"Received context: {context}")
    update: telebot.types.Update = telebot.types.Update.de_json(json.loads(event['body']))
    tb.process_new_updates([update])
    return


def load_files(document: telebot.types.Document, workdir: str) -> str:
    """
    Loads the files from the Telegram message into the local filesystem and checks structure.

    Args:
        document: Telegram document object.
        workdir: path to the working directory.

    Returns: None
    """
    # clear any remnants from previous runs (in case instance is already spun up)
    subprocess.run(["mkdir", "-p", workdir], cwd=ROOT_PATH)
    path: str = ROOT_PATH + workdir
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
    subprocess.run(["rm", "-rf", workdir], cwd=ROOT_PATH)
    logging.debug(f"Removed {workdir} from {ROOT_PATH}")
    return


def latex_convert(ipynb_path: str, workdir: str) -> str:
    """
    Converts the ipynb file into a pdf using latex.

    Args:
        ipynb_path: path to the ipynb file.
        workdir: path to the working directory.

    Returns: path of pdf.
    """
    completed_process: subprocess.CompletedProcess = subprocess.run(
        ["jupyter", "nbconvert", "--to", "pdf", ipynb_path],
        cwd=ROOT_PATH + workdir + "/",
        timeout=60,
    )
    logging.debug(f"Completed process: {completed_process}")
    if completed_process.returncode != 0:
        logging.error(
            f"Error converting {ipynb_path} to pdf: {completed_process.stdout}"
        )
        raise Exception()
    pdf_path: str = os.path.splitext(ipynb_path)[0] + ".pdf"
    return pdf_path


def chromium_convert(ipynb_path: str, workdir: str) -> str:
    """
    Converts the ipynb file into a pdf using chromium and pyppeteer.

    Args:
        ipynb_path: path to the ipynb file.
        workdir: path to the working directory.

    Returns: path of pdf.
    """
    completed_process: subprocess.CompletedProcess = subprocess.run(
        ["jupyter", "nbconvert", ipynb_path, "--to", "webpdf", "--disable-chromium-sandbox"],
        cwd=ROOT_PATH + workdir + "/",
        timeout=60,
    )
    logging.debug(f"Completed process: {completed_process}")
    if completed_process.returncode != 0:
        logging.error(
            f"Error converting {ipynb_path} to pdf: {completed_process.stdout}"
        )
        raise Exception()
    pdf_path: str = os.path.splitext(ipynb_path)[0] + ".pdf"
    return pdf_path


@tb.message_handler(commands=['start'])
def start_handler(message: telebot.types.Message) -> None:
    logging.debug("Captured start command")
    tb.send_message(
        message.chat.id,
        'Welcome! Please upload your files to convert, or use the command /help for detailed instructions.'
    )
    return


@tb.message_handler(commands=['help'])
def help_handler(message: telebot.types.Message) -> None:
    logging.debug("Captured help command")
    tb.send_message(
        message.chat.id,
        "To convert something, send me a zip file or ipynb file. I'll convert it to a pdf and send it back to you. "
        "If your file is a zip file, it must contain exactly one ipynb file."
    )
    return


@tb.message_handler(content_types=['document'])
def document_handler(message: telebot.types.Message) -> None:
    logging.debug("Captured document")
    workdir: str = uuid.uuid4().hex
    executor: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=1)
    pbar = tqdm(
        total=100,
        desc="Converting: ",
        unit=" %",
        bar_format="{desc}: {percentage:3.0f}%|{bar}|{postfix}",
        colour="black",
        postfix="Loading files...",
        leave=True,
        token=os.environ["TELEGRAM_TOKEN"],
        chat_id=message.chat.id
    )

    def progress_bar(process: Future, target: int, expected_time: float) -> Any:
        timestep: float = 0.5
        time_elapsed: float = 0
        initial_n: int = pbar.n
        while not process.done():
            time.sleep(timestep)
            if time_elapsed < expected_time:
                pbar.update(timestep * (target - initial_n) / expected_time)
                time_elapsed += timestep
        return process.result()

    try:
        future: Future = executor.submit(load_files, (message.document, workdir))
        ipynb_path: str = progress_bar(future, 20, 1)
    except TypeError as error:
        logging.debug(error)
        pbar.colour = "red"
        pbar.postfix = "Error: Wrong file type"
        tb.send_message(message.chat.id, "Looks like you uploaded the wrong file types. Please try again.")
        cleanup_files(workdir)
        return
    except Exception as error:
        logging.error(error)
        pbar.colour = "red"
        pbar.postfix = "Error: Files could not be loaded"
        tb.send_message(message.chat.id, "Looks like there's a problem with your files. Please try again.")
        cleanup_files(workdir)
        return
    pbar.postfix = "Converting to pdf via LaTeX..."
    try:
        future: Future = executor.submit(latex_convert, (ipynb_path, workdir))
        pdf_path: str = progress_bar(future, 60, 8)
    except Exception as error:
        logging.error(error)
        pbar.postfix = "Latex conversion failed. Trying chromium..."
        try:
            future: Future = executor.submit(chromium_convert, (ipynb_path, workdir))
            pdf_path: str = progress_bar(future, 90, 20)
        except Exception as error:
            logging.debug(error)
            pbar.colour = "red"
            pbar.postfix = "Error: Conversion failed"
            tb.send_message(message.chat.id, "Chromium conversion failed as well :( Check your files again, "
                                             "or file a bug report at "
                                             "https://github.com/robert-dumitru/ipynbconverterbot/issues/new")
            cleanup_files(workdir)
            return
    pbar.n = 99
    pbar.postfix = "Uploading pdf..."
    tb.send_document(message.chat.id, open(f"{ROOT_PATH + workdir}/{pdf_path}", 'rb'))
    pbar.colour = "green"
    pbar.postfix = "Done! \U00002728\U0001F370\U00002728"
    cleanup_files(workdir)
    return


@tb.message_handler(func=lambda message: True)
def default_handler(message: telebot.types.Message) -> None:
    logging.debug("Captured other message")
    tb.send_message(message.chat.id, "That's not a valid command! Check /help for the full list of commands you can"
                                     " use with me.")
    return

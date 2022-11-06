import os
import logging
import uuid
import time
from concurrent.futures import ProcessPoolExecutor, Future
from typing import Any
import telebot
from tqdm.contrib.telegram import tqdm

from util import load_files, cleanup_files, latex_convert, chromium_convert

# set this to a higher level if you don't want so many logging messages
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
telebot.logger.setLevel(logging.DEBUG)

tb: telebot.TeleBot = telebot.TeleBot(os.environ["TELEGRAM_TOKEN"])


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
    # runtime variables
    root_path: str = os.environ["ROOT_PATH"]
    workdir: str = uuid.uuid4().hex
    # Initialize progress bar
    pbar = tqdm(
        total=100,
        desc="Converting: ",
        unit=" %",
        bar_format="{desc}{percentage:3.0f}%|{bar}|{postfix}",
        postfix="Loading files...",
        leave=True,
        token=os.environ["TELEGRAM_TOKEN"],
        chat_id=message.chat.id
    )

    with ProcessPoolExecutor(max_workers=1) as executor:
        def progress_bar(process: Future, target: int, expected_time: float) -> Any:
            timestep: float = 1
            time_elapsed: float = 0
            initial_n: int = pbar.n
            while not process.done():
                time.sleep(timestep)
                if time_elapsed < expected_time:
                    pbar.update(timestep * (target - initial_n) / expected_time)
                    time_elapsed += timestep
            try:
                return process.result()
            except Exception as e:
                logging.warning(e)
                return

        try:
            future: Future = executor.submit(load_files, tb, message.document, workdir)
            ipynb_path: str = progress_bar(future, 20, 1)
        except TypeError as error:
            logging.debug(error)
            pbar.postfix = "Error: Wrong file type"
            pbar.close()
            tb.send_message(message.chat.id, "Looks like you uploaded the wrong file types. Please try again.")
            cleanup_files(workdir)
            return
        except Exception as error:
            logging.error(error)
            pbar.postfix = "Error: Files could not be loaded"
            pbar.close()
            tb.send_message(message.chat.id, "Looks like there's a problem with your files. Please try again.")
            cleanup_files(workdir)
            return
        pbar.postfix = "Converting to pdf via LaTeX..."
        try:
            future: Future = executor.submit(latex_convert, ipynb_path, workdir)
            pdf_path: str = progress_bar(future, 60, 8)
            if not pdf_path:
                raise Exception()
        except Exception as error:
            logging.error(error)
            pbar.postfix = "Latex conversion failed. Trying chromium..."
            try:
                future: Future = executor.submit(chromium_convert, ipynb_path, workdir)
                pdf_path: str = progress_bar(future, 90, 20)
                if not pdf_path:
                    raise Exception()
            except Exception as error:
                logging.debug(error)
                pbar.postfix = "Error: Conversion failed"
                pbar.close()
                tb.send_message(message.chat.id, "Looks like you ran into a bug :( Check your files again, "
                                                 "or file a bug report at "
                                                 "https://github.com/robert-dumitru/ipynbconverterbot/issues/new")
                cleanup_files(workdir)
                return
        pbar.postfix = "Uploading pdf..."
        try:
            pbar.n = 80
            future: Future = executor.submit(
                tb.send_document(message.chat.id, open(f"{root_path + workdir}/{pdf_path}", 'rb'))
            )
            progress_bar(future, 100, 2)
            pbar.n = 100
            pbar.postfix = "Done! \U00002728\U0001F370\U00002728"
            pbar.close()
        except Exception as error:
            logging.error(error)
            pbar.postfix = "ERROR: Upload failed"
            pbar.close()
            tb.send_message(message.chat.id, "Looks like you ran into a bug :( Check your files again, "
                                             "or file a bug report at "
                                             "https://github.com/robert-dumitru/ipynbconverterbot/issues/new")
            return
        cleanup_files(workdir)
    return


@tb.message_handler(func=lambda message: True)
def default_handler(message: telebot.types.Message) -> None:
    logging.debug("Captured other message")
    tb.send_message(message.chat.id, "That's not a valid command! Check /help for the full list of commands you can"
                                     " use with me.")
    return


if __name__ == "__main__":
    tb.infinity_polling()

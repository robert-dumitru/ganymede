import os
import json
import logging
import uuid
import telebot

from file_utils import load_files
from conversion_utils import latex_convert, chromium_convert

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
telebot.logger.setLevel(logging.DEBUG)
tb: telebot.TeleBot = telebot.TeleBot(os.environ["TELEGRAM_TOKEN"], threaded=False)

# Workaround so that different requests in ec2 don't conflict
workdir: str = "/home/ubuntu/ipynbconverterbot/tmp/" + uuid.uuid4().hex


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


@tb.message_handler(commands=['start'])
def start_handler(message: telebot.types.Message) -> None:
    logging.debug("Captured start command")
    tb.send_message(
        message.chat.id,
        'Welcome! Please upload your files to convert, or use the command /help for detailed instructions.'
    )


@tb.message_handler(commands=['help'])
def help_handler(message: telebot.types.Message) -> None:
    logging.debug("Captured help command")
    tb.send_message(
        message.chat.id,
        "To convert something, send me a zip file or ipynb file. I'll convert it to a pdf and send it back to you. "
        "If your file is a zip file, it must contain exactly one ipynb file."
    )


@tb.message_handler(content_types=['document'])
def document_handler(message: telebot.types.Message) -> None:
    logging.debug("Captured document")
    tb.send_message(message.chat.id, "Loading your files...")
    try:
        ipynb_path: str = load_files(tb, message.document, workdir)
    except TypeError as error:
        logging.debug(error)
        tb.send_message(message.chat.id, "Looks like you uploaded the wrong file types. Please try again.")
        return
    except Exception as error:
        logging.error(error)
        tb.send_message(message.chat.id, "Looks like there's a problem with your files. Please try again.")
        return
    tb.send_message(message.chat.id, 'Got your files! Hang tight while I convert them...')
    try:
        pdf_path: str = latex_convert(ipynb_path, workdir)
    except Exception as error:
        logging.error(error)
        tb.send_message(message.chat.id, "Latex conversion failed. Trying chromium...")
        try:
            pdf_path: str = chromium_convert(ipynb_path, workdir)
        except Exception as error:
            logging.debug(error)
            tb.send_message(message.chat.id, "Chromium conversion failed as well :( Check your files again, "
                                             "or file a bug report at "
                                             "https://github.com/robert-dumitru/ipynbconverterbot/issues/new")
            return
    tb.send_document(message.chat.id, open(f"{workdir}/{pdf_path}", 'rb'))
    tb.send_message(message.chat.id, "Done! \U00002728\U0001F370\U00002728")


@tb.message_handler(func=lambda message: True)
def default_handler(message: telebot.types.Message) -> None:
    logging.debug("Captured other message")
    tb.send_message(message.chat.id, "That's not a valid command! Check /help for the full list of commands you can"
                                     " use with me.")

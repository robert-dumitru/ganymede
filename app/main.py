import os
import json
import telebot
import logging

from util.file_utils import load_files, check_files
from util.conversion_utils import latex_convert, chromium_convert
from util.exceptions import FileError

logger = telebot.logger
logger.setLevel(logging.DEBUG)

http_200 = {'statusCode': 200}


def handler(event: dict, context: dict) -> dict:
    """
    This function handles messages from the user and directs them to the appropriate conversion function.

    Args:
        event: AWS Gateway event
        context: AWS Lambda context

    Returns: HTTP response
    """
    logging.debug(f"Received event: {event}")
    logging.debug(f"Received context: {context}")
    tb: telebot.TeleBot = telebot.TeleBot(os.environ["TELEGRAM_TOKEN"])
    update: telebot.types.Update = telebot.types.Update.de_json(json.loads(event['body']))
    tb.process_new_messages([update.message])

    @tb.message_handler(commands=['start'])
    def start_handler(message: telebot.types.Message) -> dict:
        tb.send_message(
            message.chat.id,
            'Welcome! Please upload your files to convert, or use the command /help for detailed instructions.'
        )
        return http_200

    @tb.message_handler(commands=['help'])
    def help_handler(message: telebot.types.Message) -> dict:
        tb.send_message(
            message.chat.id,
            "placeholder"  # TODO: add message
        )
        return http_200

    @tb.message_handler(content_types=['document'])
    def document_handler(message: telebot.types.Message) -> dict:
        tb.send_message(message.chat.id, "Loading your files...")
        workdir = "/tmp"
        try:
            load_files(tb, message.document, workdir)
            ipynb_path: str = check_files(workdir)
        except FileError as error:
            logging.debug(error)
            tb.send_message(message.chat.id, "placeholder")  # TODO: add message
            return http_200
        except Exception as error:
            logging.error(error)
            tb.send_message(message.chat.id, "placeholder")  # TODO: add message
            return http_200
        tb.send_message(message.chat.id, 'Got your files! Hang tight while I convert them...')
        try:
            pdf_path = latex_convert(workdir, ipynb_path)
        except Exception as e:
            logging.debug(e)
            tb.send_message(message.chat.id, "placeholder")  # TODO: add message
            try:
                pdf_path: str = chromium_convert(workdir, ipynb_path)
            except Exception as e:
                logging.debug(e)
                tb.send_message(message.chat.id, "placeholder")  # TODO: add message
                # TODO: upload prompt?
                return http_200
        tb.send_document(message.chat.id, open(f"{workdir}/{pdf_path}", 'rb'))
        tb.send_message(message.chat.id, 'placeholder')  # TODO: add message
        return http_200

    @tb.message_handler(lambda message: True)
    def default_handler(message: telebot.types.Message) -> dict:
        tb.send_message(message.chat.id, "placeholder")  # TODO: add message
        return http_200

    return http_200


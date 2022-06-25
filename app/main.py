import os
import json
# noinspection PyPackageRequirements
import telebot
import logging

from util.file_utils import load_files, check_files
from util.conversion_utils import latex_convert, chromium_convert
from util.exceptions import NoNBFileError, TooManyNBsFileError

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
    bot: telebot.TeleBot = telebot.TeleBot(os.environ["TELEGRAM_TOKEN"])
    update: telebot.types.Update = telebot.types.Update.de_json(json.loads(event['body']))
    bot.process_new_messages([update.message])

    @bot.message_handler(commands=['start'])
    def start_handler(message: telebot.types.Message) -> dict:
        bot.send_message(
            message.chat.id,
            'Welcome! Please upload your files to convert, or use the command /help for detailed instructions.'
        )
        return http_200

    @bot.message_handler(commands=['help'])
    def help_handler(message: telebot.types.Message) -> dict:
        bot.send_message(
            message.chat.id,
            "placeholder"  # TODO: add message
        )
        return http_200

    @bot.message_handler(content_types=['document'])
    def document_handler(message: telebot.types.Message) -> dict:
        bot.send_message(message.chat.id, "Loading your files...")
        try:
            load_files(message.document)
            check_files()
        except TooManyNBsException:
            bot.send_message(message.chat.id, "placeholder")  # TODO: add message
        except Exception as e:
            logging.debug(e)
            bot.send_message(message.chat.id, "placeholder")  # TODO: add message
        bot.send_message(message.chat.id, 'Got your files! Hang tight while I convert them...')
        try:
            latex_convert()
        except Exception as e:
            logging.debug(e)
            bot.send_message(message.chat.id, "placeholder")  # TODO: add message
            try:
                chromium_convert()
            except Exception as e:
                logging.debug(e)
                bot.send_message(message.chat.id, "placeholder")  # TODO: add message
                # TODO: upload prompt?
                return http_200
        bot.send_document(message.chat.id, open(f"tmp/NOTEBOOK.pdf", 'rb'))
        bot.send_message(message.chat.id, 'placeholder')  # TODO: add message
        return http_200

    @bot.message_handler(lambda message: True)
    def default_handler(message: telebot.types.Message) -> dict:
        bot.send_message(message.chat.id, "placeholder")  # TODO: add message
        return http_200

    return http_200


import logging
import json
import boto3
import telebot

import bot


def passthrough(event: dict, context: dict) -> dict:
    """
    This function replies to the gateway and passes on the event to the process_messages function.

    Args:
        event: AWS Gateway event.
        context: AWS Lambda context.

    Returns: HTTP response.
    """
    logging.debug(f"Received event: {event}")
    logging.debug(f"Received context: {context}")
    boto3.client("lambda").invoke(
        FunctionName="ipynb-converter-dev-messages",
        InvocationType="Event",
        Payload=json.dumps(event),
    )
    return {"statusCode": 200}


def converter(event: dict, context: dict) -> None:
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
    bot.tb.process_new_updates([update])
    return

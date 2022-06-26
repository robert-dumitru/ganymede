import logging
import json
import boto3


def handler(event: dict, context: dict) -> dict:
    """
    This function replies to the gateway and passes on the event to the process_messages function.

    Args:
        event: AWS Gateway event.
        context: AWS Lambda context.

    Returns: HTTP response.
    """
    logging.debug(f"Received event: {event}")
    logging.debug(f"Received context: {context}")
    boto3.client('lambda').invoke(
        FunctionName='ipynb-converter-dev-messages',
        InvocationType='Event',
        Payload=json.dumps(event)
    )
    return {'statusCode': 200}

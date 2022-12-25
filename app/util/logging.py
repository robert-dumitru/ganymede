import logging
import os
import aiopg
from telebot.types import Message


async def log_to_db(message: Message, result: str) -> None:
    """
    Logs a call to the bot to a PostgreSQL database.

    Args:
        message: message that user sent.
        result: result of processing.

    Returns: None.
    """
    try:
        async with aiopg.connect(
            host=os.getenv("PGHOST"),
            database=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD")
        ) as conn:
            async with conn.cursor() as cur:
                query = "INSERT INTO ipynb_table (user_id, exit_message, file_id) VALUES (%s, %s, %s);"
                values = (message.from_user.id, result, message.document.file_id)
                await cur.execute(query, values)
        logging.debug(f"Successfully logged query with values {values}")
        return
    except Exception as e:
        # this catches when no credentials are set up.
        logging.error(e)
        logging.warning(f"Was not able to log these values to database: {values}")
        return

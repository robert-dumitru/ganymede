import asyncio
import logging
from http import HTTPStatus
import os
from temporalio.client import Client

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
)
from telegram.ext import filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome! Please upload your files to convert, or use the command /help for detailed instructions.",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="To convert something, send me a zip file or ipynb file. I'll convert it to a pdf and send it back to you. If your file is a zip file, it must contain exactly one ipynb file.",
    )


async def convert_document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # download document
    file = await context.bot.get_file(update.message.document.file_id)
    file_path = await file.download()
    logger.info(f"Downloaded file to {file_path}")
    #TODO: add temporal calls and loading bars here
    file_id = ...
    client = await Client.connect(
        os.getenv("TEMPORAL_ADDRESS", "localhost:7233"), namespace="ganymede"
    )
    workflow = await client.execute_workflow(...)


async def fallback_file_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I can only convert zip, tar, and ipynb files. Please use the command /help for detailed instructions.",
    )


async def fallback_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, that's not a valid command. Please use the command /help for detailed instructions.",
    )


async def main() -> None:
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # register handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(
        MessageHandler(
            filters.Document.ZIP
            | filters.Document.TARGZ
            | filters.Document.FileExtension("ipynb", case_sensitive=True),
            convert_document_handler,
        )
    )
    application.add_handler(MessageHandler(filters.Document.ALL, fallback_file_msg))
    application.add_handler(MessageHandler(filters.ALL, fallback_cmd))

    # Set up webserver
    application.run_webhook(
        listem="0.0.0.0",
        port=8443,
        secret_token=os.getenv("WEBHOOK_SECRET"),
        webhook_url=os.getenv("WEBHOOK_URL"),  # TODO: update this
    )


if __name__ == "__main__":
    asyncio.run(main())

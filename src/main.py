import logging
import os

from prometheus_client import start_http_server, Summary, Counter
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from util import convert_from_update, spinner

file_processing = Summary("file_process_time", "Time spent processing file", ["user_id"])
errors = Counter("errors", "Number of errors", ["user_id"])
messages = Counter("messages", "Number of messages", ["user_id"])

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    messages.labels(user_id=update.message.from_user.id).inc()
    await update.message.reply_text(
        "Welcome! Please upload your files to convert, or use the /help command for detailed instructions."
    )


async def help_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    messages.labels(user_id=update.message.from_user.id).inc()
    await update.message.reply_text(
        "To convert something, send me a zip file or ipynb file. I'll convert it to a pdf and send it back to you. "
        "If your file is a zip file, it must contain exactly one ipynb file."
    )


async def fallback_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    messages.labels(user_id=update.message.from_user.id).inc()
    await update.message.reply_text(
        "Sorry, I didn't understand that. Please check the /help command to discover what I can do."
    )


async def error_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    errors.labels(user_id=update.message.from_user.id).inc()
    await update.message.reply_text(
        "Sorry, something went wrong. Please check your files, or open an issue at "
        "https://github.com/robert-dumitru/ganymede/issues"
    )


@spinner("Converting your file, hang tight...")
async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    with file_processing.labels(user_id=update.message.from_user.id).time():
        messages.labels(user_id=update.message.from_user.id).inc()
        await convert_from_update(update)


def main() -> None:
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    application.add_handlers(
        [
            CommandHandler("start", start_msg),
            CommandHandler("help", help_msg),
            MessageHandler(
                filters.Document.ZIP
                | filters.Document.TARGZ
                | filters.Document.FileExtension("ipynb"),
                process_file,
            ),
            MessageHandler(filters.ALL, fallback_msg),
        ]
    )
    application.add_error_handler(error_msg)

    # start prometheus metrics server
    start_http_server(9090)

    # start telegram server
    application.run_webhook(
        listen="0.0.0.0",
        port=os.getenv("PORT"),
        webhook_url=os.getenv("WEBHOOK_URL"),
        secret_token=os.getenv("WEBHOOK_SECRET"),
    )


if __name__ == "__main__":
    main()

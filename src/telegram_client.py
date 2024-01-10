import logging
import os

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome! Please upload your files to convert, or use the command /help for detailed instructions."
    )


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.

    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    application.add_handlers(
        [
            CommandHandler("start", start),
        ]
    )

    application.run_webhook(listen="0.0.0.0", port=os.getenv("PORT"), webhook_url=os.getenv("WEBHOOK_URL"))


if __name__ == "__main__":
    main()


import asyncio
import logging
from dataclasses import dataclass
from http import HTTPStatus
import os

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ExtBot,
    TypeHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@dataclass
class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""

    user_id: int
    payload: str


class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    """
    Custom CallbackContext class that makes `user_data` available for updates of type
    `WebhookUpdate`.
    """

    @classmethod
    def from_update(
        cls,
        update: object,
        application: "Application",
    ) -> "CustomContext":
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)


async def start_cmd(update: Update, context: CustomContext) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text="Welcome! Please upload your files to convert, or use the command /help for detailed instructions.",
    )


async def help_cmd(update: Update, context: CustomContext) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        reply_to_message_id=update.effective_message.message_id,
        text="To convert something, send me a zip file or ipynb file. I'll convert it to a pdf and send it back to you. If your file is a zip file, it must contain exactly one ipynb file."
    )


async def main() -> None:
    context_types = ContextTypes(context=CustomContext)
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).updater(None).context_types(context_types).build()

    # register handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))

    # Pass webhook settings to telegram
    await application.bot.set_webhook(url=f"{os.getenv('WEBHOOK_URL')}/telegram", allowed_updates=Update.ALL_TYPES)

    # Set up webserver
    async def telegram(request: Request) -> Response:
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        await application.update_queue.put(Update.de_json(data=await request.json(), bot=application.bot))
        return Response()

    async def custom_updates(request: Request) -> PlainTextResponse:
        """
        Handle incoming webhook updates by also putting them into the `update_queue` if
        the required parameters were passed correctly.
        """
        try:
            user_id = int(request.query_params["user_id"])
            payload = request.query_params["payload"]
        except KeyError:
            return PlainTextResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content="Please pass both `user_id` and `payload` as query parameters.",
            )
        except ValueError:
            return PlainTextResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content="The `user_id` must be a string!",
            )

        await application.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
        return PlainTextResponse("Thank you for the submission! It's being forwarded.")

    async def health(_: Request) -> PlainTextResponse:
        """For the health endpoint, reply with a simple plain text message."""
        return PlainTextResponse(content="The bot is still running fine :)")

    starlette_app = Starlette(
        routes=[
            Route("/telegram", telegram, methods=["POST"]),
            Route("/healthcheck", health, methods=["GET"]),
            Route("/submitpayload", custom_updates, methods=["POST", "GET"]),
        ]
    )
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=starlette_app,
            port=os.getenv("PORT", 8000),
            use_colors=True,
            host="0.0.0.0",
        )
    )

    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())

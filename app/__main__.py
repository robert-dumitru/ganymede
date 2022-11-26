import logging
import uuid
import os
import asyncio
import aiofiles
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message
from tqdm.contrib.telegram import tqdm

from util import (
    load_files,
    cleanup_files,
    latex_convert,
    chromium_convert,
    coro_tqdm_progress,
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
telebot.logger.setLevel(logging.DEBUG)

bot: AsyncTeleBot = AsyncTeleBot(os.getenv("IPYNB_TG_TOKEN"))


@bot.message_handler(commands=["start"])
async def start_handler(message: Message) -> None:
    logging.debug("Captured start command")
    await bot.reply_to(
        message,
        "Welcome! Please upload your files to convert, or use the command /help for detailed instructions.",
    )


@bot.message_handler(commands=["help"])
async def help_handler(message: Message) -> None:
    logging.debug("Captured help command")
    await bot.reply_to(
        message,
        "To convert something, send me a zip file or ipynb file. I'll convert it to a pdf and send it back to you. "
        "If your file is a zip file, it must contain exactly one ipynb file.",
    )


@bot.message_handler(content_types=["document"])
async def document_handler(message: Message) -> None:
    workdir = "/tmp/ipynb-bot-" + uuid.uuid4().hex
    pbar = tqdm(
        total=100,
        desc="Converting: ",
        unit=" %",
        bar_format="{desc}{percentage:3.0f}%|{bar}|{postfix}",
        postfix="Loading files...",
        leave=True,
        token=os.getenv("IPYNB_TG_TOKEN"),
        chat_id=message.chat.id,
    )
    try:
        try:
            ipynb_path = await coro_tqdm_progress(
                load_files(bot, message.document, workdir), pbar, 20, 1
            )
        except TypeError as e:
            logging.warning(e)
            pbar.postfix = "Error: Files could not be loaded"
            pbar.close()
            await asyncio.gather(
                bot.reply_to(
                    message,
                    "Looks like there's a problem with your files. Please try again.",
                ),
                cleanup_files(workdir),
            )
            return
        pbar.postfix = "Converting to pdf via LaTeX..."
        try:
            pdf_path = await coro_tqdm_progress(
                latex_convert(ipynb_path, workdir), pbar, 60, 10
            )
            if not pdf_path:
                raise SystemError("No PDF path found!")
        except SystemError as e:
            logging.warning(e)
            pdf_path = await coro_tqdm_progress(
                chromium_convert(ipynb_path, workdir), pbar, 90, 10
            )
        pbar.postfix = "Uploading pdf..."
        pbar.n = 80
        upload = bot.send_document(
            message.chat.id,
            aiofiles.open(f"{workdir}/{pdf_path}", "rb"),
            reply_to_message_id=message.id,
        )
        await coro_tqdm_progress(upload, pbar, 100, 2)
        pbar.n = 100
        pbar.postfix = "Done! \U00002728\U0001F370\U00002728"
        pbar.close()
        await cleanup_files(workdir)
    except Exception as error:
        logging.error(error)
        pbar.postfix = "ERROR: Unknown failure"
        pbar.close()
        await asyncio.gather(
            bot.reply_to(
                message,
                "Looks like you ran into a bug :( Check your files again, or file a bug report at "
                "https://github.com/robert-dumitru/ipynbconverterbot/issues/new",
            ),
            cleanup_files(workdir),
        )
        return


@bot.message_handler(func=lambda message: True)
async def default_handler(message: Message) -> None:
    logging.debug("Captured other message")
    await bot.reply_to(
        message,
        "That's not a valid command! Check /help for the full list of commands you can use with me.",
    )


asyncio.run(bot.polling(non_stop=True))

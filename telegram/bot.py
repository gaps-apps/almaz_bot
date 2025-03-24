import hashlib
import random

from aiohttp import web

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import get_from_env
from logger import logfire

conf = get_from_env()

TOKEN = conf["BOT_TOKEN"]

WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = 8000
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = hashlib.sha256(random.randbytes(128)).hexdigest()
BASE_WEBHOOK_URL = conf["WEBHOOK_BASE"]

# All handlers should be attached to the Router (or Dispatcher)
router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    with logfire.span("received /start; answering") as span:
        await message.answer(f"Hello, {hbold(message.from_user.full_name)}!")


@router.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like text, photo, sticker etc.)
    """
    with logfire.span("echo handler; answering") as span:
        try:
            await message.send_copy(chat_id=message.chat.id)
        except TypeError:
            # But not all the types is supported to be copied so need to handle it
            await message.answer("Nice try!")


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET
    )
    logfire.info(f"Webhook URL: \"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}\" Secret: \"{WEBHOOK_SECRET}\"")


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    logfire.info("Webhook deleted.")


def serve_webhook() -> None:
    dp = Dispatcher()

    dp.include_router(router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

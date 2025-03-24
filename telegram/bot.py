import hashlib
import random

from aiohttp import web

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import conf
from logger import logfire

from .handlers import setup_handlers

TOKEN = conf["BOT_TOKEN"]

WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = hashlib.sha256(random.randbytes(128)).hexdigest()
BASE_WEBHOOK_URL = conf["WEBHOOK_BASE"]


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET
    )
    logfire.info(
        f'Webhook URL: "{BASE_WEBHOOK_URL}{WEBHOOK_PATH}" Secret: "{WEBHOOK_SECRET}"'
    )


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    logfire.info("Webhook deleted.")


def serve_webhook() -> None:
    dp = Dispatcher()
    router = Router()

    setup_handlers(router)
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

    web.run_app(app, host=conf["WEB_SERVER_HOST"], port=int(conf["WEB_SERVER_PORT"]))

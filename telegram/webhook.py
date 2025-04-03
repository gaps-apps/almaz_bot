import hashlib
import random

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import (SimpleRequestHandler,
                                            setup_application)
from aiohttp import web

from config import conf
from logger import logfire

BASE_WEBHOOK_URL = conf["WEBHOOK_BASE"]
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = hashlib.sha256(random.randbytes(256)).hexdigest()
WEBHOOK_URL = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"

WEBHOOK_SUCCESS = f'Webhook URL: "{WEBHOOK_URL}" Secret: "{WEBHOOK_SECRET}"'
WEBHOOK_DELETED = "Webhook deleted."


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    logfire.info(WEBHOOK_SUCCESS)


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    logfire.info(WEBHOOK_DELETED)


def get_webhook_app(dp: Dispatcher, bot: Bot) -> web.Application:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    return app

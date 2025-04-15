import hashlib
import random
import logging

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import conf
from lombardis.protocols import LombardisAPI
from repository.protocols import UsersRepo

WEBHOOK_BASE = conf["WEBHOOK_BASE"]
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_BASE}{WEBHOOK_PATH}"

WEBHOOK_SECRET = hashlib.sha256(random.randbytes(256)).hexdigest()

WEBHOOK_SUCCESS = f'Webhook URL: "{WEBHOOK_URL}" Secret: "{WEBHOOK_SECRET}"'
WEBHOOK_DELETED = "Webhook deleted."

logger = logging.getLogger(__name__)


def get_webhook_app(
    dp: Dispatcher, bot: Bot, users: UsersRepo, lombardis: LombardisAPI
) -> web.Application:

    async def on_startup() -> None:
        await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
        logger.info(WEBHOOK_SUCCESS)

    async def on_shutdown() -> None:
        await bot.delete_webhook()
        await users.close()
        logger.info(WEBHOOK_DELETED)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        users=users,
        lombardis=lombardis,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    return app

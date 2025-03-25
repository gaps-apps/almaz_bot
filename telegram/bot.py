from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import conf

from .handlers import setup_handlers

TOKEN = conf["BOT_TOKEN"]


def get_dispatcher() -> tuple[Dispatcher, Bot]:
    dp = Dispatcher()
    router = Router()

    setup_handlers(router)
    dp.include_router(router)

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    return dp, bot

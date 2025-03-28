from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import conf

from .handlers import start_router, menu_router, payment_router


def get_dispatcher() -> tuple[Dispatcher, Bot]:
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(payment_router)

    return dp, Bot(
        token=conf["BOT_TOKEN"], default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

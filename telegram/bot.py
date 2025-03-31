from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties


from config import conf

from .handlers import start_router, loans_router


def get_dispatcher() -> tuple[Dispatcher, Bot]:
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(loans_router)

    return dp, Bot(
        token=conf["BOT_TOKEN"], default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

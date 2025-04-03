import asyncio

from aiogram import Bot
from aiohttp import web

from config import conf

from lombardis.api import LombardisAPI, LombardisAPIProtocol
from repository.users import UsersRepo

from telegram.bot import get_dispatcher
from telegram.webhook import get_webhook_app
from telegram.handlers.commands_menu import set_bot_commands

from tests.fakes.lombardis import LombardisAPIFake

users = UsersRepo()


async def init(bot: Bot) -> None:
    await asyncio.gather(
        users.bootstrap(),
        set_bot_commands(bot),
    )


if __name__ == "__main__":
    dp, bot = get_dispatcher()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(init(bot))

    lombardis: LombardisAPIProtocol = LombardisAPI()

    if conf["DEMO_MODE"].lower() == "true":
        lombardis = LombardisAPIFake()

    if conf["POLLING"].lower() == "true":
        # polling mode
        loop.run_until_complete(dp.start_polling(bot, users=users, lombardis=lombardis))
    else:
        # webhook mode
        web.run_app(
            get_webhook_app(dp, bot, users, lombardis),
            host=conf["WEB_SERVER_HOST"],
            port=int(conf["WEB_SERVER_PORT"]),
        )

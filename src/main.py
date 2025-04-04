import asyncio

from aiogram import Bot
from aiohttp import web

from config import conf

from lombardis.protocols import LombardisAPI
from lombardis.api import LombardisAsyncHTTP

from repository.protocols import UsersRepo
from repository.users import UsersRepoSQLite

from telegram.bot import get_dispatcher
from telegram.webhook import get_webhook_app
from telegram.handlers.commands_menu import set_bot_commands

from tests.fakes.lombardis import LombardisFake


async def init(bot: Bot, users: UsersRepo) -> None:
    tasks = [
        users.bootstrap(),
        set_bot_commands(bot),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    dp, bot = get_dispatcher()

    lombardis: LombardisAPI
    users: UsersRepo

    if conf["DEMO_MODE"].lower() == "true":
        lombardis = LombardisFake()
        users = UsersRepoSQLite(db_name=":memory:")
    else:
        lombardis = LombardisAsyncHTTP()
        users = UsersRepoSQLite()

    loop.run_until_complete(init(bot, users))
    dp.shutdown.register(users.close)

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

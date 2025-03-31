import asyncio

from aiohttp import web

from repository.clients import fetch_and_update_local_db
from repository.users import UsersRepo

from telegram.webhook import get_webhook_app
from telegram.handlers import commands_menu
from telegram.bot import get_dispatcher

from config import conf

users = UsersRepo()


async def init(bot):
    await asyncio.gather(
        users.bootstrap(),
        fetch_and_update_local_db(),
        commands_menu.set_bot_commands(bot),
    )


if __name__ == "__main__":
    dp, bot = get_dispatcher()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(init(bot))

    if conf["POLLING"].lower() == "true":
        # polling mode
        loop.run_until_complete(dp.start_polling(bot, users=users))

    else:
        # webhook mode
        web.run_app(
            get_webhook_app(dp, bot),
            host=conf["WEB_SERVER_HOST"],
            port=int(conf["WEB_SERVER_PORT"]),
        )

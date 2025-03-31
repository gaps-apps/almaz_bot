import asyncio

from aiohttp import web

from repository.clients import fetch_and_update_local_db
from repository.users import create_users_table
from config import conf

from telegram.webhook import get_webhook_app
from telegram.bot import get_dispatcher


if __name__ == "__main__":
    asyncio.run(create_users_table())
    asyncio.run(fetch_and_update_local_db())

    if conf["POLLING"].lower() == "true":
        # polling mode
        dp, bot = get_dispatcher()
        asyncio.run(dp.start_polling(bot))

    else:
        # webhook mode
        web.run_app(
            get_webhook_app(*get_dispatcher()),
            host=conf["WEB_SERVER_HOST"],
            port=int(conf["WEB_SERVER_PORT"]),
        )

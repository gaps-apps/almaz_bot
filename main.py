import asyncio

from repository.clients import fetch_and_update_local_db
from repository.users import create_users_table

from telegram.bot import get_dispatcher

if __name__ == "__main__":
    asyncio.run(create_users_table())
    asyncio.run(fetch_and_update_local_db())

    dp, bot = get_dispatcher()
    asyncio.run(dp.start_polling(bot))

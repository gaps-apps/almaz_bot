import asyncio

from lombardis.api import LombardisAPI
from repository.clients import fetch_and_store_clients
from repository.users import create_users_table
from telegram.bot import serve_webhook

from config import conf

if __name__ == "__main__":
    asyncio.run(create_users_table())

    lombardis = LombardisAPI(conf["LOMBARDIS_USER"], conf["LOMBARDIS_PASSWORD"])
    asyncio.run(fetch_and_store_clients(api=lombardis))

    serve_webhook()

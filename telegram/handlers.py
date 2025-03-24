from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from auth import authorize, add_admin
from config import conf
from logger import logfire, log_span


def setup_handlers(router: Router) -> None:
    @router.message(CommandStart())
    @authorize
    @log_span("/start")
    async def command_start_handler(message: Message) -> None:
        """
        This handler receives messages with `/start` command
        """
        await message.answer(f"Привет, {hbold(message.from_user.first_name)}!")

    @router.message(Command("admin"))
    @log_span("/admin")
    async def command_admin_handler(message: Message) -> None:
        """
        This handler processes the `/admin` command with a secret parameter.
        """
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Ошибка: необходимо передать секретный ключ.")
            logfire.info(
                f"Попытка вызова /admin без параметра от {message.from_user.id}"
            )
            return

        secret = args[1]
        if secret != conf["ADMIN_SECRET"]:
            await message.answer("Ошибка: неверный секретный ключ.")
            logfire.info(
                f"Неудачная попытка авторизации в админке от {message.from_user.id}"
            )
            return

        add_admin(message.from_user.id)
        await message.answer("Вы успешно добавлены в список администраторов!")
        logfire.info(f"Пользователь {message.from_user.id} добавлен в администраторы.")

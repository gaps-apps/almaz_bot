from functools import wraps
from aiogram.types import Message

from logger import logfire

power_users = []


def add_admin(chat_id) -> None:
    power_users.append(chat_id)


def is_admin(chat_id) -> bool:
    return chat_id in power_users


def authorize(handler):
    """
    Декоратор для проверки авторизации пользователя перед вызовом обработчика.
    Если пользователь не авторизован, отправляет сообщение и не вызывает хэндлер.
    """

    @wraps(handler)
    async def wrapper(message: Message, *args, **kwargs):
        if not is_admin(message.chat.id):
            await message.answer(
                "Бот находится в стадии разработки и доступен только администраторам и разработчикам."
            )
            logfire.info(
                f"Unauthorized user id={message.chat.id} name={message.from_user.full_name}"
            )
            return
        return await handler(message, *args, **kwargs)

    return wrapper

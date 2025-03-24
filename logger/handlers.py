from functools import wraps
from aiogram.types import Message

from . import logfire


def log_span(command_name: str):
    def decorator(handler):
        @wraps(handler)
        async def wrapper(message: Message, *args, **kwargs):
            with logfire.span(
                f"Received {command_name}; text: {message.text}, user: {message.from_user.id} ({message.from_user.full_name})"
            ):
                return await handler(message, *args, **kwargs)

        return wrapper

    return decorator

from aiogram import Bot
from aiogram.types import BotCommand

from .text_constants import HELP_COMMAND_DESCRIPTION, START_COMMAND_DESCRIPTION


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="/start", description=START_COMMAND_DESCRIPTION),
    ]
    await bot.set_my_commands(commands)

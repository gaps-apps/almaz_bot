from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.markdown import hitalic

from lombardis.api import LombardisAPI

from repository.dto import UserDTO
from repository.users import UsersRepo

from .helpers import replace_english_with_russian

from .text_constants import (
    AUTH_NEEDED,
    BIRTHDAY_PLEASE,
    CLIENT_NOT_FOUND,
    HELP_INSTRUCTIONS,
    INVALID_LOAN_MESSAGE,
    LOAN_NUMBER_PLEASE,
    LOANS_MENU_TEXT,
    INVALID_BIRTHDAY_MESSAGE,
    GREETINGS,
)


class AuthState(StatesGroup):
    waiting_for_birthday = State()
    waiting_for_loan_number = State()


router = Router()


@router.message(CommandStart())
async def command_start_handler(
    message: Message, state: FSMContext, users: UsersRepo
) -> None:
    if await state.get_state() not in [
        AuthState.waiting_for_birthday,
        AuthState.waiting_for_loan_number,
    ]:
        if not await users.user_exists(message.from_user.id):
            await message.answer(HELP_INSTRUCTIONS)
            await message.answer(AUTH_NEEDED)
            await message.answer(BIRTHDAY_PLEASE)
            await state.set_state(AuthState.waiting_for_birthday)
        else:
            keyboard = ReplyKeyboardBuilder()
            keyboard.button(text=LOANS_MENU_TEXT)
            keyboard.adjust(1)

            user = await users.get_user_by_params({"chat_id": message.from_user.id})
            await message.answer(
                GREETINGS.format(full_name=f"{hitalic(user.full_name)}"),
                reply_markup=keyboard.as_markup(resize_keyboard=True),
            )


@router.message(AuthState.waiting_for_birthday, F.text)
async def birthday_handler(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit() or len(message.text) != 8:
        await message.answer(INVALID_BIRTHDAY_MESSAGE)
        return

    await state.update_data(birthday=message.text)
    await message.answer(LOAN_NUMBER_PLEASE)
    await state.set_state(AuthState.waiting_for_loan_number)


@router.message(AuthState.waiting_for_loan_number, F.text)
async def loan_number_handler(
    message: Message, state: FSMContext, users: UsersRepo
) -> None:
    user_data = await state.get_data()
    birthday = user_data.get("birthday")
    loan_number = replace_english_with_russian(message.text.strip())
    if len(loan_number) != 8:
        await message.answer(INVALID_LOAN_MESSAGE)
        return

    client_id = await LombardisAPI().get_client_id(f"{birthday} {loan_number}")

    if client_id is None:
        await message.answer(CLIENT_NOT_FOUND)
        await state.clear()
        return

    client_details = await LombardisAPI().get_client_details(client_id)
    FULL_NAME_PARTS = [
        client_details.surname,
        client_details.name,
        client_details.patronymic,
    ]
    full_name = " ".join(FULL_NAME_PARTS)
    await users.add_user(
        UserDTO(message.from_user.id, full_name, client_id, client_details.phone)
    )
    await state.clear()

    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=LOANS_MENU_TEXT)
    keyboard.adjust(1)

    user = await users.get_user_by_params({"chat_id": message.from_user.id})
    await message.answer(
        GREETINGS.format(full_name=f"{hitalic(user.full_name)}"),
        reply_markup=keyboard.as_markup(resize_keyboard=True),
    )

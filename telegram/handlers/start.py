from typing import Optional

import logfire
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.markdown import hitalic
from aiogram_calendar import (DialogCalendar, DialogCalendarCallback,
                              get_user_locale)

from lombardis.api import LombardisAPI
from repository.dto import UserDTO
from repository.users import UsersRepo

from .helpers import replace_english_with_russian
from .text_constants import (AUTH_NEEDED, BIRTHDAY_PLEASE, GREETINGS,
                             INVALID_BIRTHDAY_MESSAGE, INVALID_LOAN_MESSAGE,
                             LOAN_NUMBER_PLEASE, LOANS_MENU_TEXT)


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
        if message.from_user is None:
            logfire.error("Received message without sender info.")
            return  # Ignore messages without sender info

        if not await users.user_exists(message.from_user.id):
            await message.answer(AUTH_NEEDED)
            await message.answer(
                BIRTHDAY_PLEASE,
                reply_markup=await DialogCalendar(
                    locale=await get_user_locale(message.from_user)
                ).start_calendar(1989),
            )
            await state.set_state(AuthState.waiting_for_birthday)
        else:
            keyboard = ReplyKeyboardBuilder()
            keyboard.button(text=LOANS_MENU_TEXT)
            keyboard.adjust(1)

            user: Optional[UserDTO] = await users.get_user(
                {"chat_id": message.from_user.id}
            )
            if user is None:
                logfire.error(
                    f"User with chat_id {message.from_user.id} not found in database."
                )
                return

            await message.answer(
                GREETINGS.format(full_name=f"{hitalic(user.full_name)}"),
                reply_markup=keyboard.as_markup(resize_keyboard=True),
            )


@router.message(AuthState.waiting_for_birthday, F.text)
async def birthday_handler(message: Message, state: FSMContext) -> None:
    if message.text is None or not message.text.isdigit() or len(message.text) != 8:
        await message.answer(INVALID_BIRTHDAY_MESSAGE)
        return

    await state.update_data(birthday=message.text)
    await message.answer(LOAN_NUMBER_PLEASE)
    await state.set_state(AuthState.waiting_for_loan_number)


@router.message(AuthState.waiting_for_loan_number, F.text)
async def loan_number_handler(
    message: Message, state: FSMContext, users: UsersRepo
) -> None:
    if message.text is None:
        logfire.error("Received empty loan number input.")
        return

    user_data = await state.get_data()
    birthday = user_data.get("birthday")
    if not birthday:
        logfire.error("Birthday is missing from state data. Restarting authentication.")
        await state.clear()
        return

    loan_number = replace_english_with_russian(message.text.strip())
    if len(loan_number) != 8:
        await message.answer(INVALID_LOAN_MESSAGE)
        return

    client_id = await LombardisAPI().get_client_id(f"{birthday} {loan_number}")

    if client_id is None:
        logfire.warning(
            f"Client not found for birthday {birthday} and loan number {loan_number}."
        )
        await state.clear()
        return

    client_details = await LombardisAPI().get_client_details(client_id)
    if client_details is None:
        logfire.error(f"Failed to retrieve client details for client_id {client_id}.")
        return

    full_name = " ".join(
        filter(
            None,
            [client_details.surname, client_details.name, client_details.patronymic],
        )
    )

    if message.from_user is None:
        logfire.error("Received loan number input from an unknown user.")
        return

    await users.add_user(
        UserDTO(message.from_user.id, full_name, client_id, client_details.phone)
    )
    await state.clear()

    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=LOANS_MENU_TEXT)
    keyboard.adjust(1)

    user = await users.get_user({"chat_id": message.from_user.id})
    if user:
        await message.answer(
            GREETINGS.format(full_name=f"{hitalic(user.full_name)}"),
            reply_markup=keyboard.as_markup(resize_keyboard=True),
        )


@router.callback_query(AuthState.waiting_for_birthday, DialogCalendarCallback.filter())
async def process_dialog_calendar(
    callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext
) -> None:
    if callback_query.from_user is None:
        logfire.error("Received calendar callback without sender info.")
        return
    if callback_query.message is None:
        logfire.error("Received calendar callback without message object.")
        return

    selected, date = await DialogCalendar(
        locale=await get_user_locale(callback_query.from_user)
    ).process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(date.strftime("%Y%m%d"))
        await state.update_data(birthday=date.strftime("%Y%m%d"))
        await callback_query.message.answer(LOAN_NUMBER_PLEASE)
        await state.set_state(AuthState.waiting_for_loan_number)

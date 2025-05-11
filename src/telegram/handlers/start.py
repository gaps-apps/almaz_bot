import logging
from typing import Optional

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.markdown import hitalic
from aiogram_calendar import DialogCalendar, DialogCalendarCallback, get_user_locale

from lombardis.protocols import LombardisAPI
from repository.dto import User
from repository.protocols import UsersRepo

from .helpers import ensure_loan_number_format
from .text_constants import (
    AUTH_NEEDED,
    BIRTHDAY_PLEASE,
    GREETINGS,
    INVALID_BIRTHDAY_MESSAGE,
    INVALID_LOAN_MESSAGE,
    LOAN_NUMBER_PLEASE,
    LOANS_MENU_TEXT,
)

logger = logging.getLogger(__name__)


class AuthState(StatesGroup):
    waiting_for_birthday = State()
    waiting_for_loan_number = State()


router = Router()


@router.message(CommandStart())
async def command_start_handler(
    message: Message, state: FSMContext, users: UsersRepo
) -> None:
    assert message.from_user is not None

    try:
        if await state.get_state() not in [
            AuthState.waiting_for_birthday,
            AuthState.waiting_for_loan_number,
        ]:
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

                user: Optional[User] = await users.get_user(
                    {"chat_id": message.from_user.id}
                )
                if user is None:
                    logger.error(
                        f"User with chat_id {message.from_user.id} not found in database."
                    )
                    return

                await message.answer(
                    GREETINGS.format(full_name=f"{hitalic(user.full_name)}"),
                    reply_markup=keyboard.as_markup(resize_keyboard=True),
                )
    except Exception as e:
        logger.exception(f"Error in command_start_handler: {e}")


@router.message(AuthState.waiting_for_birthday, F.text)
async def birthday_handler(message: Message, state: FSMContext) -> None:
    assert message.text is not None

    if not message.text.isdigit() or len(message.text) != 8:
        await message.answer(INVALID_BIRTHDAY_MESSAGE)
        return

    await state.update_data(birthday=message.text)
    await message.answer(LOAN_NUMBER_PLEASE)
    await state.set_state(AuthState.waiting_for_loan_number)


@router.message(AuthState.waiting_for_loan_number, F.text)
async def loan_number_handler(
    message: Message,
    state: FSMContext,
    users: UsersRepo,
    lombardis: LombardisAPI,
) -> None:
    assert message.text is not None
    assert message.from_user is not None

    try:
        user_data = await state.get_data()
        birthday = user_data.get("birthday")
        if not birthday:
            logger.error(
                "Birthday is missing from state data. Restarting authentication."
            )
            await state.clear()
            return

        loan_number = ensure_loan_number_format(message.text.strip())
        if len(loan_number) != 8:
            await message.answer(INVALID_LOAN_MESSAGE)
            return

        client_id_dto = await lombardis.get_client_id(f"{birthday} {loan_number}")
        if client_id_dto is None:
            logger.warning(
                f"Client not found for birthday {birthday} and loan number {loan_number}."
            )
            await state.clear()
            return

        client_details = await lombardis.get_client_details(
            str(client_id_dto.client_id)
        )
        if client_details is None:
            logger.error(
                f"Failed to retrieve client details for client_id {client_id_dto.client_id}."
            )
            return

        await users.add_user(
            User(
                message.from_user.id,
                client_details.full_name,
                str(client_id_dto.client_id),
                client_details.phone,
            )
        )
        await state.clear()

        keyboard = ReplyKeyboardBuilder()
        keyboard.button(text=LOANS_MENU_TEXT)
        keyboard.adjust(1)

        user = await users.get_user({"chat_id": message.from_user.id})
        if user is None:
            logger.error(
                f"User with chat_id {message.from_user.id} not found in database."
            )
            return

        await message.answer(
            GREETINGS.format(full_name=f"{hitalic(user.full_name)}"),
            reply_markup=keyboard.as_markup(resize_keyboard=True),
        )
    except Exception as e:
        logger.exception(f"Error in loan_number_handler: {e}")


@router.callback_query(AuthState.waiting_for_birthday, DialogCalendarCallback.filter())
async def process_dialog_calendar(
    callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext
) -> None:
    assert callback_query.message is not None
    assert callback_query.from_user is not None

    selected, date = await DialogCalendar(
        locale=await get_user_locale(callback_query.from_user)
    ).process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(date.strftime("%Y%m%d"))
        await state.update_data(birthday=date.strftime("%Y%m%d"))
        await callback_query.message.answer(LOAN_NUMBER_PLEASE)
        await state.set_state(AuthState.waiting_for_loan_number)

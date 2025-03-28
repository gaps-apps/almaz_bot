import asyncio

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from lombardis.schemas import ClientDetailsResponse
from lombardis.api import LombardisAPI

from repository import clients
from repository import users

from .helpers import (
    is_valid_phone_number,
    send_sms_code,
    format_phone_number,
)

from .text_constants import (
    START_MESSAGE,
    TIMEOUT_MESSAGE,
    CODE_SENT_MESSAGE,
    REGISTRATION_SUCCESS_MESSAGE,
    INVALID_CODE_MESSAGE,
    INVALID_PHONE_MESSAGE,
)

from .menu import debt_menu_handler


class RegistrationState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()


router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        if not await users.user_exists(message.from_user.id):
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Отправить мой номер", request_contact=True)],
                ],
                resize_keyboard=True,
            )
            await message.answer(START_MESSAGE, reply_markup=keyboard)
            await state.set_state(RegistrationState.waiting_for_phone)
        else:
            await debt_menu_handler(message)


@router.message(RegistrationState.waiting_for_phone, lambda message: message.contact)
async def phone_number_handler(message: Message, state: FSMContext) -> None:
    if is_valid_phone_number(message.contact.phone_number):

        phone_number = format_phone_number(message.contact.phone_number)

        client_id = await clients.get_or_update_client_id(phone_number)

        if client_id is None:
            await message.answer("Клиент с таким номером телефона не найден. Верификация номера отменена.")
            state.clear()
            return

        verification_code = await send_sms_code(phone_number)

        await state.update_data(
            phone=message.contact.phone_number,
            code=verification_code,
            client_id=client_id,
        )

        await message.answer(CODE_SENT_MESSAGE)
        await state.set_state(RegistrationState.waiting_for_code)

        await asyncio.sleep(60)
        current_state = await state.get_state()
        if current_state == RegistrationState.waiting_for_code.state:
            await message.answer(TIMEOUT_MESSAGE)
            await state.clear()
    else:
        await message.answer(INVALID_PHONE_MESSAGE)


@router.message(RegistrationState.waiting_for_code, F.text)
async def code_verification_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if message.text == str(data.get("code")):
        phone_number = format_phone_number(data.get("phone"))

        client_id = data.get("client_id")

        client_details: ClientDetailsResponse = await LombardisAPI().get_client_details(
            client_id
        )
        full_name = " ".join(
            [client_details.surname, client_details.name, client_details.patronymic]
        )
        await users.add_user(
            message.from_user.id,
            full_name,
            client_id,
            phone_number,
        )
        await message.answer(REGISTRATION_SUCCESS_MESSAGE)
        await state.clear()
        await debt_menu_handler(message)

    else:
        await message.answer(INVALID_CODE_MESSAGE)

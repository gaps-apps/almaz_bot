import asyncio

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.markdown import hitalic

from lombardis.api import LombardisAPI

from repository.dto import UserDTO
from repository import clients
from repository.users import UsersRepo


from .helpers import (
    is_valid_phone_number,
    send_sms_code,
    format_phone_number,
)

from .text_constants import (
    CLIENT_NOT_FOUND,
    LOANS_MENU_TEXT,
    SEND_MY_CONTACT_BUTTON,
    PLEASE_VERIFY_NUMBER,
    TIMEOUT_MESSAGE,
    CODE_SENT_MESSAGE,
    INVALID_CODE_MESSAGE,
    INVALID_PHONE_MESSAGE,
    AUTH_SUCCESS,
)


class RegistrationState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()


router = Router()


@router.message(CommandStart())
async def command_start_handler(
    message: Message, state: FSMContext, users: UsersRepo
) -> None:
    # if not in a process of verification
    if await state.get_state() not in [
        RegistrationState.waiting_for_code,
        RegistrationState.waiting_for_phone,
    ]:
        # if user is not registered yet
        if not await users.user_exists(message.from_user.id):
            keyboard = ReplyKeyboardBuilder()
            keyboard.button(text=SEND_MY_CONTACT_BUTTON, request_contact=True)

            await message.answer(
                PLEASE_VERIFY_NUMBER,
                reply_markup=keyboard.as_markup(resize_keyboard=True),
            )
            await state.set_state(RegistrationState.waiting_for_phone)
        else:
            # menu for verified user
            keyboard = ReplyKeyboardBuilder()
            keyboard.button(text=LOANS_MENU_TEXT)
            keyboard.adjust(1)

            user = await users.get_user_by_params({"chat_id": message.from_user.id})
            user: UserDTO
            await message.answer(
                AUTH_SUCCESS.format(full_name=f"{hitalic(user.full_name)}"),
                reply_markup=keyboard.as_markup(resize_keyboard=True),
            )


@router.message(RegistrationState.waiting_for_phone, lambda message: message.contact)
async def phone_number_handler(message: Message, state: FSMContext) -> None:
    if is_valid_phone_number(message.contact.phone_number):
        # received valid phone number for verification
        phone_number = format_phone_number(message.contact.phone_number)
        client_id = await clients.get_or_update_client_id(phone_number)

        if client_id is None:
            # clients db was updated, but client phone was not found.
            # exit early, assuming client entered wrong number
            await message.answer(CLIENT_NOT_FOUND)
            await state.clear()
            return

        # verify number for known client
        verification_code = await send_sms_code(phone_number)

        # pass client data through FSM
        await state.update_data(
            phone=message.contact.phone_number,
            code=verification_code,
            client_id=client_id,
        )

        # code sent
        await message.answer(CODE_SENT_MESSAGE)
        await state.set_state(RegistrationState.waiting_for_code)

        # code input timeout here.
        await asyncio.sleep(60)
        current_state = await state.get_state()
        # if no state change, reset FSM, because it's timeout
        if current_state == RegistrationState.waiting_for_code.state:
            await message.answer(TIMEOUT_MESSAGE)
            await state.clear()
    else:
        await message.answer(INVALID_PHONE_MESSAGE)


@router.message(RegistrationState.waiting_for_code, F.text)
async def code_verification_handler(
    message: Message, state: FSMContext, users: UsersRepo
) -> None:
    # received code for verification
    data = await state.get_data()  # got client data from FSM
    if message.text == str(data.get("code")):
        # verified successfully

        # gettting client details and save it to local database.
        phone_number = format_phone_number(data.get("phone"))
        client_id = data.get("client_id")
        client_details = await LombardisAPI().get_client_details(client_id)

        FULL_NAME_ELEMENTS = [
            client_details.surname,
            client_details.name,
            client_details.patronymic,
        ]
        full_name = " ".join(FULL_NAME_ELEMENTS)
        await users.add_user(
            message.from_user.id,
            full_name,
            client_id,
            phone_number,
        )
        # reset FSM, because verification is over by success.
        await state.clear()
        # redirect to /start as known user
        await command_start_handler(message, state)

    else:
        await message.answer(INVALID_CODE_MESSAGE)

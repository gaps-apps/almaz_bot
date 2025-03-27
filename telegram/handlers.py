import asyncio

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
)

from lombardis.schemas import ClientDetailsResponse
from lombardis.api import LombardisAPI

from repository import clients
from repository import users

from .helpers import (
    answer_debt_information,
    answer_loans_information,
    is_valid_phone_number,
    send_sms_code,
    format_phone_number,
)

from .text_constants import (
    INVALID_PHONE_MESSAGE,
    START_MESSAGE,
    TIMEOUT_MESSAGE,
    CODE_SENT_MESSAGE,
    REGISTRATION_SUCCESS_MESSAGE,
    INVALID_CODE_MESSAGE,
    DEBT_MENU_TEXT,
    LOANS_MENU_TEXT,
    PAYLOAN_SELECTION_MESSAGE,
)


class RegistrationState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()


def setup_handlers(router: Router) -> None:
    @router.message(CommandStart())
    async def command_start_handler(message: Message, state: FSMContext) -> None:
        if await state.get_state() is None:
            if not await users.user_exists(message.from_user.id):

                await message.answer(START_MESSAGE)
                await state.set_state(RegistrationState.waiting_for_phone)
            else:
                await debt_menu_handler(message)

    @router.message(F.text == DEBT_MENU_TEXT)
    async def debt_menu_handler(message: Message):
        await answer_debt_information(message)

    @router.message(F.text == LOANS_MENU_TEXT)
    async def loans_menu_handler(message: Message):
        await answer_loans_information(message)

    @router.message(RegistrationState.waiting_for_phone)
    async def phone_number_handler(message: Message, state: FSMContext) -> None:
        if is_valid_phone_number(message.text):
            verification_code = await send_sms_code(message.text)
            await state.update_data(phone=message.text, code=verification_code)
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
            client_id = await clients.get_client_id_by_phone(phone_number)

            client_details: ClientDetailsResponse = (
                await LombardisAPI().get_client_details(client_id)
            )
            full_name = " ".join(
                [client_details.surname, client_details.name, client_details.patronymic]
            )
            user = await users.add_user(
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

    @router.callback_query(lambda c: c.data.startswith("payloan_"))
    async def process_loan_payment_callback(callback: CallbackQuery) -> None:
        loan_id = callback.data.split("_")[1]
        await callback.message.answer(PAYLOAN_SELECTION_MESSAGE.format(loan_id=loan_id))
        await callback.answer()

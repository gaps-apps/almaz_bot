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

from repository.dto import UserDTO

from .helpers import (
    answer_debt_information,
    answer_loans_information,
    is_valid_phone_number,
    send_sms_code,
    format_phone_number,
)

# TODO вынести все текстовые данные в отдельный файл.


class RegistrationState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()


def setup_handlers(router: Router) -> None:
    @router.message(CommandStart())
    async def command_start_handler(message: Message, state: FSMContext) -> None:
        if await state.get_state() is None:
            if not await users.user_exists(message.from_user.id):

                await message.answer(
                    "Введите номер телефона клиента ломбарда. Для подтверждения личности вам придёт смс с кодом."
                )
                await state.set_state(RegistrationState.waiting_for_phone)
            else:
                await debt_menu_handler(message)

    @router.message(F.text == "💰 Общая информация")
    async def debt_menu_handler(message: Message):
        user: UserDTO = await users.get_user_by_params(
            {"chat_id": message.from_user.id}
        )

        basic_info = await clients.get_basic_info_by_params(
            {"phone_number": user.phone_number}
        )
        if basic_info is None:
            # локальная база клиентов обновляется при запуске бота.
            # если клиент свежее времени обновления базы, то нужно её обновить.
            await clients.fetch_and_update_local_db()
            basic_info = await clients.get_basic_info_by_params(
                {"phone_number": user.phone_number}
            )
        await answer_debt_information(
            message, client=basic_info, full_name=user.full_name
        )

    @router.message(F.text == "💳 Залоги и оплата")
    async def loans_menu_handler(message: Message):
        await answer_loans_information(message)

    @router.message(RegistrationState.waiting_for_phone)
    async def phone_number_handler(message: Message, state: FSMContext) -> None:
        if is_valid_phone_number(message.text):
            verification_code = await send_sms_code(message.text)
            await state.update_data(phone=message.text, code=verification_code)
            await message.answer(
                "Код подтверждения отправлен. Пожалуйста, введите его в течение 1 минуты."
            )
            await state.set_state(RegistrationState.waiting_for_code)

            await asyncio.sleep(60)
            current_state = await state.get_state()
            if current_state == RegistrationState.waiting_for_code.state:
                await message.answer(
                    "Время ожидания кода истекло. Пожалуйста, отправьте команду /start заново."
                )
                await state.clear()
        else:
            await message.answer(
                "Ошибка: введите корректный номер телефона в формате +79991234567 или 89991234567."
            )

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
            await message.answer("Регистрация успешно завершена!")
            await state.clear()
            await debt_menu_handler(message)

        else:
            await message.answer("Ошибка: неверный код. Попробуйте ещё раз.")

    @router.callback_query(lambda c: c.data.startswith("payloan_"))
    async def process_loan_payment_callback(callback: CallbackQuery) -> None:
        loan_id = callback.data.split("_")[1]
        await callback.message.answer(
            f"✅ Вы выбрали оплату долга {loan_id}. Пока оплата недоступна."
        )
        await callback.answer()


##TODO
# + 1. в залогах номер залогового билета, сумма займа и проценты по залогу
# + 2. оплата количество процентов по залогу сумма оплаты.
# 3. при нажатии на залог показать карточку залогового имущества, оплатить проценты.
# 4. залоговые билеты, залоговое имущество.
# 5. проценты мандарина должны быть включены в сумму оплаты.

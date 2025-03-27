import re
import random
import asyncio
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.markdown import hbold, hitalic

from auth import add_admin
from config import conf
from logger import logfire

from lombardis.schemas import ClientDetailsResponse, ClientLoanResponse
from lombardis.api import LombardisAPI

from repository import clients
from repository import users

from repository.dto import ClientBasicInfoDTO, UserDTO

# TODO вынести все текстовые данные в отдельный файл.


class RegistrationState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()


def is_valid_phone_number(phone: str) -> bool:
    logfire.info(f"Validating phone: {phone}")
    return bool(re.fullmatch(r"(?:\+7|7|8)\d{10}", phone))


def format_phone_number(phone: str) -> str:
    """Formats a validated phone number to start with +7."""
    phone = re.sub(r"[^\d]", "", phone)  # Remove any non-numeric characters
    if phone.startswith("8") or phone.startswith("7"):
        phone = "+7" + phone[-10:]  # Ensure it starts with +7 and keep last 10 digits
    return phone


def format_client_info(client: ClientBasicInfoDTO, full_name: str) -> str:
    """Formats client debt information into a readable message in Russian."""
    nearest_payment = (
        datetime.fromisoformat(client.nearest_payment_date).strftime("%d.%m.%Y")
        if client.nearest_payment_date
        else "Нет данных"
    )

    return (
        f"{hbold(full_name)}\n\n"
        f"{hbold('💰 Полный долг:')} {hitalic(f'{client.full_debt:.2f} ₽')}\n"
        f"{hbold('💸 Проценты:')} {hitalic(f'{client.full_interest_debt:.2f} ₽')}\n"
        f"{hbold('⏳ Просроченный долг:')} {hitalic(f'{client.overdue_debt:.2f} ₽')}\n"
        f"{hbold('📉 Просроченные проценты:')} {hitalic(f'{client.overdue_interest_debt:.2f} ₽')}\n\n"
        f"{hbold('📅 Ближайшая дата платежа:')} {nearest_payment}\n"
    )


def get_loans_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой 'Залоги и оплата'."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Залоги и оплата", callback_data=f"loans")]
        ]
    )
    return keyboard


async def send_client_info(
    message: Message, client: ClientBasicInfoDTO, full_name: str
) -> None:
    """Sends formatted client information as a message."""
    formatted_text = format_client_info(client, full_name)
    keyboard = get_loans_keyboard()
    await message.answer(formatted_text, reply_markup=keyboard, parse_mode="HTML")


async def send_sms_code(phone: str) -> int:
    code = random.randint(100000, 999999)
    logfire.info(f"Sending SMS with code {code} to {phone}")
    return code


async def loans_handler(message: Message) -> None:
    user: UserDTO = await users.get_user_by_params({"chat_id": message.chat.id})

    client_loans: ClientLoanResponse = await LombardisAPI().get_client_loans(
        user.client_id
    )

    if not client_loans.Loans:
        await message.answer("❌ У клиента нет активных залогов.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{loan.pawnBillNumber}",
                    callback_data=f"payloan_{loan.LoanID}",
                )
            ]
            for loan in client_loans.Loans
        ]
    )

    await message.answer(f"📜 Залоговые билеты:", reply_markup=keyboard)


def setup_handlers(router: Router) -> None:
    @router.message(CommandStart())
    async def command_start_handler(message: Message, state: FSMContext) -> None:
        if await state.get_state() is None:
            if not await users.user_exists(message.from_user.id):
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="💰 Общая информация")],
                        [KeyboardButton(text="📜 Залоговые билеты")],
                    ],
                    resize_keyboard=True,
                )
                await message.answer(
                    "Введите номер телефона клиента ломбарда. Для подтверждения личности вам придёт смс с кодом.",
                    reply_markup=keyboard,
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
        await send_client_info(message, client=basic_info, full_name=user.full_name)

    @router.message(F.text == "📜 Залоговые билеты")
    async def loans_menu_handler(message: Message):
        await loans_handler(message)

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

    @router.message(Command("admin"))
    async def command_admin_handler(message: Message) -> None:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("Ошибка: необходимо передать секретный ключ.")
            logfire.info(
                f"Попытка вызова /admin без параметра от {message.from_user.id}"
            )
            return

        secret = args[1]
        if secret != conf["ADMIN_SECRET"]:
            await message.answer("Ошибка: неверный секретный ключ.")
            logfire.info(
                f"Неудачная попытка авторизации в админке от {message.from_user.id}"
            )
            return

        add_admin(message.from_user.id)
        await message.answer("Вы успешно добавлены в список администраторов!")
        logfire.info(f"Пользователь {message.from_user.id} добавлен в администраторы.")

    @router.callback_query(lambda c: c.data.startswith("loans"))
    async def process_loans_callback(callback: CallbackQuery) -> None:
        await callback.answer()

        # Вызываем команду /loans принудительно
        await loans_handler(callback.message)

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

import re
import random
from datetime import datetime

from aiogram.utils.markdown import hbold, hitalic
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from repository.dto import ClientDebtDTO, UserDTO
from lombardis.schemas import ClientLoanResponse
from lombardis.api import LombardisAPI
from repository import users
from repository import clients
from logger import logfire

from .text_constants import (
    DEBT_INFO_HEADER,
    DEBT_MENU_TEXT,
    INTEREST_DEBT_HEADER,
    LOANS_MENU_TEXT,
    OVERDUE_DEBT_HEADER,
    OVERDUE_INTEREST_DEBT_HEADER,
    NEAREST_PAYMENT_HEADER,
    NO_ACTIVE_LOANS,
    PAWN_TICKET_HEADER,
)


def is_valid_phone_number(phone: str) -> bool:
    logfire.info(f"Validating phone: {phone}")
    return bool(re.fullmatch(r"(?:\+7|7|8)\d{10}", phone))


def format_phone_number(phone: str) -> str:
    """Formats a validated phone number to start with +7."""
    phone = re.sub(r"[^\d]", "", phone)  # Remove any non-numeric characters
    if phone.startswith("8") or phone.startswith("7"):
        phone = "+7" + phone[-10:]  # Ensure it starts with +7 and keep last 10 digits
    return phone


def format_client_info(client: ClientDebtDTO, full_name: str) -> str:
    """Formats client debt information into a readable message in Russian."""
    nearest_payment = (
        datetime.fromisoformat(client.nearest_payment_date).strftime("%d.%m.%Y")
        if client.nearest_payment_date
        else "Нет данных"
    )

    return (
        f"{hbold(full_name)}\n\n"
        f"{hbold(DEBT_INFO_HEADER)} {hitalic(f'{client.full_debt:.2f} ₽')}\n"
        f"{hbold(INTEREST_DEBT_HEADER)} {hitalic(f'{client.full_interest_debt:.2f} ₽')}\n"
        f"{hbold(OVERDUE_DEBT_HEADER)} {hitalic(f'{client.overdue_debt:.2f} ₽')}\n"
        f"{hbold(OVERDUE_INTEREST_DEBT_HEADER)} {hitalic(f'{client.overdue_interest_debt:.2f} ₽')}\n\n"
        f"{hbold(NEAREST_PAYMENT_HEADER)} {nearest_payment}\n"
    )


async def send_sms_code(phone: str) -> int:
    code = random.randint(100000, 999999)
    logfire.info(f"Sending SMS with code {code} to {phone}")
    return code


async def answer_debt_information(message: Message) -> None:
    user: UserDTO = await users.get_user_by_params({"chat_id": message.from_user.id})

    debt = await clients.get_basic_info_by_params({"phone_number": user.phone_number})

    if debt is None:
        # локальная база клиентов обновляется при запуске бота.
        # если клиент свежее времени обновления базы, то нужно её обновить.
        await clients.fetch_and_update_local_db()
        debt = await clients.get_basic_info_by_params(
            {"phone_number": user.phone_number}
        )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DEBT_MENU_TEXT)],
            [KeyboardButton(text=LOANS_MENU_TEXT)],
        ],
        resize_keyboard=True,
    )
    formatted_text = format_client_info(debt, user.full_name)
    
    await message.answer(formatted_text, reply_markup=keyboard, parse_mode="HTML")


async def answer_loans_information(message: Message) -> None:
    user: users.UserDTO = await users.get_user_by_params({"chat_id": message.chat.id})

    client_loans: ClientLoanResponse = await LombardisAPI().get_client_loans(
        user.client_id
    )

    if not client_loans.Loans:
        await message.answer(NO_ACTIVE_LOANS)
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

    await message.answer(PAWN_TICKET_HEADER, reply_markup=keyboard)

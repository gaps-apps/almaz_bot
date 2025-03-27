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

from repository.dto import ClientDebtDTO
from lombardis.schemas import ClientLoanResponse
from lombardis.api import LombardisAPI
from repository import users
from logger import logfire


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
        f"{hbold('💰 Полный долг:')} {hitalic(f'{client.full_debt:.2f} ₽')}\n"
        f"{hbold('💸 Проценты:')} {hitalic(f'{client.full_interest_debt:.2f} ₽')}\n"
        f"{hbold('⏳ Просроченный долг:')} {hitalic(f'{client.overdue_debt:.2f} ₽')}\n"
        f"{hbold('📉 Просроченные проценты:')} {hitalic(f'{client.overdue_interest_debt:.2f} ₽')}\n\n"
        f"{hbold('📅 Ближайшая дата платежа:')} {nearest_payment}\n"
    )


async def send_sms_code(phone: str) -> int:
    code = random.randint(100000, 999999)
    logfire.info(f"Sending SMS with code {code} to {phone}")
    return code


async def answer_debt_information(
    message: Message, client: ClientDebtDTO, full_name: str
) -> None:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Общая информация")],
            [KeyboardButton(text="💳 Залоги и оплата")],
        ],
        resize_keyboard=True,
    )
    """Sends formatted client information as a message."""
    formatted_text = format_client_info(client, full_name)
    await message.answer(formatted_text, reply_markup=keyboard, parse_mode="HTML")


async def answer_loans_information(message: Message) -> None:
    user: users.UserDTO = await users.get_user_by_params({"chat_id": message.chat.id})

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

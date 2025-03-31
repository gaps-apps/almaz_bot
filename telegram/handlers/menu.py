from datetime import datetime

from aiogram import Router, F

from aiogram.utils.markdown import hbold, hitalic
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from lombardis.schemas import ClientLoanResponse
from lombardis.api import LombardisAPI

from repository.dto import UserDTO
from repository import clients
from repository import users

from .text_constants import (
    DEBT_MENU_TEXT,
    LOANS_MENU_TEXT,
    DEBT_MENU_TEXT,
    LOANS_MENU_TEXT,
    NO_ACTIVE_LOANS,
    PAWN_TICKET_HEADER,
    DEBT_INFO_HEADER,
    INTEREST_DEBT_HEADER,
    OVERDUE_DEBT_HEADER,
    OVERDUE_INTEREST_DEBT_HEADER,
    NEAREST_PAYMENT_HEADER,
)

router = Router()


@router.message(F.text == DEBT_MENU_TEXT)
async def debt_menu_handler(message: Message):
    user: UserDTO = await users.get_user_by_params({"chat_id": message.from_user.id})

    debt = await clients.get_debt_by_params({"phone_number": user.phone_number})

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=DEBT_MENU_TEXT)],
            [KeyboardButton(text=LOANS_MENU_TEXT)],
        ],
        resize_keyboard=True,
    )

    nearest_payment = (
        datetime.fromisoformat(debt.nearest_payment_date).strftime("%d.%m.%Y")
        if debt.nearest_payment_date
        else "Нет данных"
    )

    formatted_text = (
        f"{hbold(user.full_name)}\n\n"
        f"{hbold(DEBT_INFO_HEADER)} {hitalic(f'{debt.full_debt:.2f} ₽')}\n"
        f"{hbold(INTEREST_DEBT_HEADER)} {hitalic(f'{debt.full_interest_debt:.2f} ₽')}\n"
        f"{hbold(OVERDUE_DEBT_HEADER)} {hitalic(f'{debt.overdue_debt:.2f} ₽')}\n"
        f"{hbold(OVERDUE_INTEREST_DEBT_HEADER)} {hitalic(f'{debt.overdue_interest_debt:.2f} ₽')}\n\n"
        f"{hbold(NEAREST_PAYMENT_HEADER)} {nearest_payment}\n"
    )

    await message.answer(formatted_text, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text == LOANS_MENU_TEXT)
async def loans_menu_handler(message: Message):
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
                    callback_data=f"loan_{loan.LoanID}",
                )
            ]
            for loan in client_loans.Loans
        ]
    )
    await message.answer(PAWN_TICKET_HEADER, reply_markup=keyboard)

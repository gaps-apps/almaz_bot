from uuid import UUID

import logfire
from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold, hitalic

from lombardis.protocols import LombardisAPI
from repository.protocols import UsersRepo

from .text_constants import (LOANS_MENU_TEXT, NO_ACTIVE_LOANS,
                             PAWN_TICKET_HEADER, PAY_LOAN_BUTTON,
                             PAYLOAN_SELECTION_MESSAGE, RUB)


class LoansCallback(CallbackData, prefix="loans"):
    loan_id: UUID


class LoanDetailsMode(StatesGroup):
    as_editing = State()
    as_new = State()


router = Router()


@router.message(F.text == LOANS_MENU_TEXT)
async def loans_menu_handler(
    message: Message,
    state: FSMContext,
    users: UsersRepo,
    lombardis: LombardisAPI,
) -> None:

    user = await users.get_user({"chat_id": message.chat.id})
    if user is None:
        logfire.error(f"User with chat_id {message.chat.id} not found in database.")
        return

    client_loans = await lombardis.get_client_loans(user.client_id)

    if client_loans is None:
        logfire.error("Failed to retrieve client loans.")
        return

    if not client_loans.Loans:
        await message.answer(NO_ACTIVE_LOANS)
        return

    keyboard = InlineKeyboardBuilder()
    for loan in client_loans.Loans:
        keyboard.button(
            text=f"{loan.pawnBillNumber}",
            callback_data=LoansCallback(loan_id=loan.LoanID),
        )
    keyboard.adjust(2)

    await message.answer(PAWN_TICKET_HEADER, reply_markup=keyboard.as_markup())
    await state.set_state(LoanDetailsMode.as_new)


@router.callback_query(LoansCallback.filter(), LoanDetailsMode.as_editing)
async def view_loans_as_editing(
    callback: CallbackQuery,
    callback_data: LoansCallback,
    state: FSMContext,
    lombardis: LombardisAPI,
) -> None:
    assert callback.bot is not None
    assert callback.message is not None

    loan_id = str(callback_data.loan_id)
    loan_details = await lombardis.get_loan_details(loan_id)
    if loan_details is None:
        logfire.error(f"Failed to retrieve loan details for loan_id {loan_id}.")
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=PAY_LOAN_BUTTON, callback_data=f"pay_{loan_id}")

    state_data = await state.get_data()

    message_id = state_data.get("loan_details_message_id")
    if message_id is None:
        logfire.error("Missing loan_details_message_id in state data.")
        return

    try:
        await callback.bot.edit_message_text(
            text="\n".join(
                [f"{hbold(loan_details.LoanNumber)}\n{loan_details.LoanSum} руб.\n"]
                + [item.Presentation for item in loan_details.Stuff]
                + [f"\nПроценты: {hitalic(loan_details.InterestsSum)} {hitalic(RUB)}\n"]
            ),
            reply_markup=keyboard.as_markup(resize_keyboard=True),
            message_id=message_id,
            chat_id=callback.message.chat.id,
        )
    finally:
        await callback.answer()


@router.callback_query(LoansCallback.filter(), LoanDetailsMode.as_new)
async def view_loan_as_new_message(
    callback: CallbackQuery,
    callback_data: LoansCallback,
    state: FSMContext,
    lombardis: LombardisAPI,
) -> None:
    assert callback.message is not None

    loan_id = str(callback_data.loan_id)
    loan_details = await lombardis.get_loan_details(loan_id)
    if loan_details is None:
        logfire.error(f"Failed to retrieve loan details for loan_id {loan_id}.")
        return

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=PAY_LOAN_BUTTON, callback_data=f"pay_{loan_id}")

    try:
        sent_message = await callback.message.answer(
            text="\n".join(
                [f"{hbold(loan_details.LoanNumber)}\n{loan_details.LoanSum} руб.\n"]
                + [item.Presentation for item in loan_details.Stuff]
                + [f"\nПроценты: {hitalic(loan_details.InterestsSum)} {hitalic(RUB)}\n"]
            ),
            reply_markup=keyboard.as_markup(resize_keyboard=True),
        )
        await state.set_data({"loan_details_message_id": sent_message.message_id})
        await state.set_state(LoanDetailsMode.as_editing)
    finally:
        await callback.answer()


@router.callback_query(lambda c: c.data.startswith("pay_"))
async def process_loan_payment_callback(callback: CallbackQuery) -> None:
    assert callback.data is not None
    assert callback.message is not None

    loan_id = callback.data.split("_")[1]

    await callback.message.answer(PAYLOAN_SELECTION_MESSAGE.format(loan_id=loan_id))
    await callback.answer()

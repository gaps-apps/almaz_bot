import logging
from uuid import UUID

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold, hitalic

from lombardis.protocols import LombardisAPI
from repository.protocols import UsersRepo

from .text_constants import (
    LOANS_MENU_TEXT,
    NO_ACTIVE_LOANS,
    PAWN_TICKET_HEADER,
    PAY_LOAN_BUTTON,
    PAYLOAN_SELECTION_MESSAGE,
    RUB,
)

logger = logging.getLogger(__name__)


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
    try:
        user = await users.get_user({"chat_id": message.chat.id})
        if user is None:
            return
        client_loans = await lombardis.get_client_loans(user.client_id)

        if not client_loans.loans:
            await message.answer(NO_ACTIVE_LOANS)
            return

        keyboard = InlineKeyboardBuilder()
        for loan in client_loans.loans:
            keyboard.button(
                text=f"{loan.pawn_bill_number}",
                callback_data=LoansCallback(loan_id=loan.loan_id),
            )
        keyboard.adjust(2)

        await message.answer(PAWN_TICKET_HEADER, reply_markup=keyboard.as_markup())
        await state.set_state(LoanDetailsMode.as_new)
    except Exception as e:
        logger.exception(f"Error in loans_menu_handler: {e}")


async def _generate_loan_details_message(
    lombardis: LombardisAPI, loan_id: str
) -> tuple[str, InlineKeyboardBuilder]:
    try:
        loan_details = await lombardis.get_loan_details(loan_id)

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=PAY_LOAN_BUTTON, callback_data=f"pay_{loan_id}")

        message_text = "\n".join(
            [f"{hbold(loan_details.loan_number)}\n{loan_details.loan_sum} руб.\n"]
            + [presentation for presentation in loan_details.stuff]
            + [f"\nПроценты: {hitalic(loan_details.interests_sum)} {hitalic(RUB)}\n"]
        )
        return message_text, keyboard
    except Exception as e:
        logger.exception(f"Error in _generate_loan_details_message: {e}")
        raise RuntimeError(f"Cant generate_loan_details for {loan_id}: {e}")


@router.callback_query(LoansCallback.filter(), LoanDetailsMode.as_editing)
async def view_loans_as_editing(
    callback: CallbackQuery,
    callback_data: LoansCallback,
    state: FSMContext,
    lombardis: LombardisAPI,
) -> None:
    assert callback.bot is not None
    assert callback.message is not None
    try:
        loan_id = str(callback_data.loan_id)
        message_text, keyboard = await _generate_loan_details_message(
            lombardis, loan_id
        )

        state_data = await state.get_data()
        message_id = state_data.get("loan_details_message_id")
        if message_id is None:
            logger.error("Missing loan_details_message_id in state data.")
            return

        await callback.bot.edit_message_text(
            text=message_text,
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
    try:
        loan_id = str(callback_data.loan_id)
        message_text, keyboard = await _generate_loan_details_message(
            lombardis, loan_id
        )

        sent_message = await callback.message.answer(
            text=message_text,
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

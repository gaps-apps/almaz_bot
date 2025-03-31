from aiogram import Router
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from lombardis.api import LombardisAPI
from lombardis.schemas import LoanDetails

from .text_constants import PAY_LOAN_BUTTON, PAYLOAN_SELECTION_MESSAGE


router = Router()


@router.callback_query(lambda c: c.data.startswith("loan_"))
async def process_loan_callback(callback: CallbackQuery) -> None:
    loan_id = callback.data.split("_")[1]
    loan_details: LoanDetails = await LombardisAPI().get_loan_details(loan_id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=PAY_LOAN_BUTTON,
                    callback_data=f"pay_{loan_id}",
                )
            ]
        ]
    )
    await callback.message.answer(
        text="\n".join(
            [f"{loan_details.LoanNumber}\n{loan_details.LoanSum} руб.\n"]
            + [item.Presentation for item in loan_details.Stuff]
            + [f"\nПроценты: {loan_details.InterestsSum} руб.\n"]
        ),
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("pay_"))
async def process_loan_payment_callback(callback: CallbackQuery) -> None:
    loan_id = callback.data.split("_")[1]
    await callback.message.answer(PAYLOAN_SELECTION_MESSAGE.format(loan_id=loan_id))
    await callback.answer()

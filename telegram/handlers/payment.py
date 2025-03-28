from aiogram import Router
from aiogram.types import CallbackQuery

from .text_constants import PAYLOAN_SELECTION_MESSAGE


router = Router()


@router.callback_query(lambda c: c.data.startswith("payloan_"))
async def process_loan_payment_callback(callback: CallbackQuery) -> None:
    loan_id = callback.data.split("_")[1]
    await callback.message.answer(PAYLOAN_SELECTION_MESSAGE.format(loan_id=loan_id))
    await callback.answer()

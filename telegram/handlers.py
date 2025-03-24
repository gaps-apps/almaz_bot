import aiosqlite
import re
import random
import asyncio
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from auth import authorize, add_admin
from config import conf
from logger import logfire, log_span
from repository.users import user_exists, add_user


class RegistrationState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()


def is_valid_phone_number(phone: str) -> bool:
    logfire.info(f"Validating phone: {phone}")
    return bool(re.fullmatch(r"(?:\+7|8)\d{10}", phone))


async def send_sms_code(phone: str) -> int:
    code = random.randint(100000, 999999)
    logfire.info(f"Sending SMS with code {code} to {phone}")
    return code


def setup_handlers(router: Router) -> None:
    @router.message(CommandStart())
    @authorize
    @log_span("/start")
    async def command_start_handler(message: Message, state: FSMContext) -> None:
        if await state.get_state() is None:
            await message.answer(f"Привет, {hbold(message.from_user.first_name)}!")
            if not await user_exists(message.from_user.id):
                await message.answer(
                    "Введите номер телефона клиента ломбарда. Для подтверждения личности вам придёт смс с кодом."
                )
                await state.set_state(RegistrationState.waiting_for_phone)

    @router.message(RegistrationState.waiting_for_phone)
    @authorize
    @log_span("phone")
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
                "Ошибка: введите корректный номер телефона в формате +79996436449 или 89996436449."
            )

    @router.message(RegistrationState.waiting_for_code, F.text)
    @authorize
    @log_span("verification")
    async def code_verification_handler(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        if message.text == str(data.get("code")):
            await add_user(
                message.from_user.id, message.from_user.full_name, data.get("phone")
            )
            await message.answer("Регистрация успешно завершена!")
            await state.clear()
        else:
            await message.answer("Ошибка: неверный код. Попробуйте ещё раз.")

    @router.message(Command("admin"))
    @log_span("/admin")
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

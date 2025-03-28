import re
import random

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


async def send_sms_code(phone: str) -> int:
    code = random.randint(100000, 999999)
    logfire.info(f"Sending SMS with code {code} to {phone}")
    return code

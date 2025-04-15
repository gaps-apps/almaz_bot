from dataclasses import dataclass


@dataclass
class User:
    """Authorizing Telegram users with this."""

    chat_id: int
    full_name: str
    client_id: str
    phone_number: str

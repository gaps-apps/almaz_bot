from dataclasses import dataclass


@dataclass
class UserDTO:
    chat_id: int
    full_name: str
    client_id: str
    phone_number: str

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClientBasicInfoDTO:
    client_id: str
    phone_number: str
    full_debt: float
    full_interest_debt: float
    overdue_debt: float
    overdue_interest_debt: float
    nearest_payment_date: Optional[str]


@dataclass
class UserDTO:
    chat_id: int
    full_name: str
    client_id: str
    phone_number: str

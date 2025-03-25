from dataclasses import dataclass
from typing import Optional


@dataclass
class ClientBasicInfoDTO:
    clientID: str
    phone: str
    fullDebt: float
    fullInterestsDebt: float
    overdueDebt: float
    overdueInterestsDebt: float
    nearestPaymentDate: Optional[str]


@dataclass
class UserDTO:
    chat_id: int
    full_name: str
    client_id: str
    phone_number: str

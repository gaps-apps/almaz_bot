from typing import List
from uuid import UUID

from pydantic.dataclasses import dataclass


@dataclass
class ClientID:
    client_id: UUID


@dataclass
class ClientDetails:
    full_name: str
    phone: str


@dataclass
class Loan:
    loan_id: UUID
    pawn_bill_number: str


@dataclass
class ClientLoans:
    loans: List[Loan]


@dataclass
class LoanDetails:
    loan_number: str
    loan_sum: float
    interests_sum: float
    stuff: List[str]

from pydantic.dataclasses import dataclass
from typing import List
from datetime import datetime
from uuid import UUID


@dataclass
class Client:
    ClientID: UUID
    PhoneNumber: str
    FullDebt: float
    FullInterestsDebt: float
    OverdueDebt: float
    OverdueInterestsDebt: float
    NearestPaymentDate: datetime


@dataclass
class ClientListResponse:
    taskStatus: int
    dataToProcess: int
    dataProcessed: int
    dataDeclined: int
    progress: float
    isError: bool
    startTime: datetime
    finishTime: datetime
    errorMessage: str
    providerID: str
    taskID: UUID
    ClientsList: List[Client]

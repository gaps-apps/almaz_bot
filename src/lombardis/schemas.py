from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic.dataclasses import dataclass


@dataclass
class ClientIDRequest:
    queryString: str


@dataclass
class ClientIDResponse:
    ClientID: UUID


@dataclass
class LoanResponse:
    LoanID: UUID
    pawnBillNumber: str
    LoanDescription: str
    ShortLoanDescription: str
    LoanDate: datetime
    PaymentDate: datetime
    Closed: bool
    fullDebt: float
    prolongationSum: float
    sellingDate: Optional[datetime]
    PaymentAvailable: bool


@dataclass
class ClientLoansResponse:
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
    Loans: List[LoanResponse]


@dataclass
class ClientDetailsResponse:
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
    clientInternalCode: str
    surname: str
    name: str
    patronymic: Optional[str]
    email: Optional[str]
    phone: str
    taxNumber: Optional[str]
    additionalInformation: List[str]
    segments: List[str]


@dataclass
class StuffItemResponse:
    Presentation: str
    Description: str
    FullDescription: str
    Status: str
    Location: str
    LocationID: str
    StuffID: str
    Price: float
    BillNumber: str
    StuffCode: str
    Gems: Optional[str]


@dataclass
class LoanDetailsResponse:
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
    taskID: str
    LoanNumber: str
    LoanDate: datetime
    PaymentDate: datetime
    SellingDate: Optional[datetime]
    LoanSum: float
    DebtSum: float
    InterestsSum: float
    Stuff: List[StuffItemResponse]
    tariffID: str
    tariffDescription: Optional[str]
    paymentAvailable: bool

from pydantic.dataclasses import dataclass
from typing import List, Optional
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


@dataclass
class Loan:
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
class ClientLoanResponse:
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
    Loans: List[Loan]


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
    surname: str
    name: str
    patronymic: Optional[str]
    email: Optional[str]
    phone: str
    taxNumber: Optional[str]
    AdditionalInformation: List[str]


@dataclass
class StuffItem:
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
class LoanDetails:
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
    Stuff: List[StuffItem]
    tariffID: str
    tariffDescription: Optional[str]
    paymentAvailable: bool

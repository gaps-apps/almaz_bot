import uuid
from datetime import datetime, timedelta

from lombardis.schemas import (ClientDetailsResponse, ClientIDResponse,
                               ClientLoansResponse, Loan, LoanDetailsResponse,
                               StuffItem)

CLIENT_ID = uuid.uuid4()
LOANS = [
    Loan(
        LoanID=uuid.uuid4(),
        pawnBillNumber="АА000142",
        LoanDescription="Займ под залог золота",
        ShortLoanDescription="Золото",
        LoanDate=datetime.now() - timedelta(days=30),
        PaymentDate=datetime.now() + timedelta(days=10),
        Closed=False,
        fullDebt=500.00,
        prolongationSum=50.00,
        sellingDate=None,
        PaymentAvailable=True,
    ),
    Loan(
        LoanID=uuid.uuid4(),
        pawnBillNumber="ББ000253",
        LoanDescription="Займ под залог техники",
        ShortLoanDescription="Техника",
        LoanDate=datetime.now() - timedelta(days=60),
        PaymentDate=datetime.now() + timedelta(days=20),
        Closed=False,
        fullDebt=800.00,
        prolongationSum=80.00,
        sellingDate=None,
        PaymentAvailable=True,
    ),
]

LOAN_DETAILS = {
    str(LOANS[0].LoanID): LoanDetailsResponse(
        taskStatus=1,
        dataToProcess=1,
        dataProcessed=1,
        dataDeclined=0,
        progress=100.0,
        isError=False,
        startTime=datetime.now() - timedelta(minutes=5),
        finishTime=datetime.now(),
        errorMessage="",
        providerID="test_provider",
        taskID=str(uuid.uuid4()),
        LoanNumber=LOANS[0].pawnBillNumber,
        LoanDate=LOANS[0].LoanDate,
        PaymentDate=LOANS[0].PaymentDate,
        SellingDate=LOANS[0].sellingDate,
        LoanSum=500.00,
        DebtSum=450.00,
        InterestsSum=50.00,
        Stuff=[
            StuffItem(
                Presentation="Кольцо с бриллиантом",
                Description="Красивое золотое кольцо с бриллиантом",
                FullDescription="Кольцо 750 пробы, 5 грамм, бриллиант 0.5 карат",
                Status="В залоге",
                Location="Отделение №1",
                LocationID="LOC1",
                StuffID="STUFF123",
                Price=1000.00,
                BillNumber="BILL12345",
                StuffCode="SC12345",
                Gems="Бриллиант",
            )
        ],
        tariffID="T1",
        tariffDescription="Стандартный тариф",
        paymentAvailable=True,
    ),
    str(LOANS[1].LoanID): LoanDetailsResponse(
        taskStatus=1,
        dataToProcess=1,
        dataProcessed=1,
        dataDeclined=0,
        progress=100.0,
        isError=False,
        startTime=datetime.now() - timedelta(minutes=5),
        finishTime=datetime.now(),
        errorMessage="",
        providerID="test_provider",
        taskID=str(uuid.uuid4()),
        LoanNumber=LOANS[1].pawnBillNumber,
        LoanDate=LOANS[1].LoanDate,
        PaymentDate=LOANS[1].PaymentDate,
        SellingDate=LOANS[1].sellingDate,
        LoanSum=800.00,
        DebtSum=750.00,
        InterestsSum=50.00,
        Stuff=[
            StuffItem(
                Presentation="Ноутбук Apple MacBook Pro",
                Description="Ноутбук Apple 16 дюймов, M1 Pro",
                FullDescription="MacBook Pro 16",
                Status="В залоге",
                Location="Отделение №2",
                LocationID="LOC2",
                StuffID="STUFF456",
                Price=2000.00,
                BillNumber="BILL67890",
                StuffCode="SC67890",
                Gems=None,
            )
        ],
        tariffID="T2",
        tariffDescription="Премиум тариф",
        paymentAvailable=True,
    ),
}


class LombardisAPIFake:

    async def get_client_details(self, client_id: str) -> ClientDetailsResponse | None:
        return ClientDetailsResponse(
            taskStatus=1,
            dataToProcess=1,
            dataProcessed=1,
            dataDeclined=0,
            progress=100.0,
            isError=False,
            startTime=datetime.now() - timedelta(minutes=5),
            finishTime=datetime.now(),
            errorMessage="",
            providerID="test_provider",
            taskID=uuid.uuid4(),
            clientInternalCode="C12345",
            surname="Иванов",
            name="Иван",
            patronymic="Иванович",
            email="ivanov@example.com",
            phone="+1234567890",
            taxNumber="1234567890",
            additionalInformation=["VIP клиент"],
            segments=["A"],
        )

    async def get_client_loans(self, client_id: str) -> ClientLoansResponse | None:
        return ClientLoansResponse(
            taskStatus=1,
            dataToProcess=1,
            dataProcessed=1,
            dataDeclined=0,
            progress=100.0,
            isError=False,
            startTime=datetime.now() - timedelta(minutes=5),
            finishTime=datetime.now(),
            errorMessage="",
            providerID="test_provider",
            taskID=uuid.uuid4(),
            Loans=LOANS,
        )

    async def get_loan_details(self, loan_id: str) -> LoanDetailsResponse | None:
        return LOAN_DETAILS.get(loan_id)

    async def get_client_id(self, query_string: str) -> str:
        return str(ClientIDResponse(ClientID=CLIENT_ID).ClientID)

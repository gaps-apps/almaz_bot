import random
import uuid

from lombardis.dto import ClientID, ClientDetails, ClientLoans, Loan, LoanDetails
from lombardis.protocols import LombardisAPI


def get_random_phone_number() -> str:
    return f"+1{random.randint(1000000000, 9999999999)}"


LOANS = [
    Loan(
        loan_id=uuid.uuid4(),
        pawn_bill_number="АА000142",
    ),
    Loan(
        loan_id=uuid.uuid4(),
        pawn_bill_number="ББ000253",
    ),
]

LOAN_DETAILS = {
    str(LOANS[0].loan_id): LoanDetails(
        loan_number=LOANS[0].pawn_bill_number,
        loan_sum=500.00,
        interests_sum=50.00,
        stuff=["Кольцо с бриллиантом"],
    ),
    str(LOANS[1].loan_id): LoanDetails(
        loan_number=LOANS[1].pawn_bill_number,
        loan_sum=800.00,
        interests_sum=50.00,
        stuff=["Ноутбук Apple MacBook Pro"],
    ),
}


class LombardisFake(LombardisAPI):

    async def get_client_id(self, query_string: str) -> ClientID:
        return ClientID(client_id=uuid.uuid4())

    async def get_client_details(self, client_id: str) -> ClientDetails:
        return ClientDetails(
            full_name="Иванов Иван Иванович",
            phone=get_random_phone_number(),
        )

    async def get_client_loans(self, client_id: str) -> ClientLoans:
        return ClientLoans(loans=LOANS)

    async def get_loan_details(self, loan_id: str) -> LoanDetails:
        result = LOAN_DETAILS.get(loan_id)
        if result is None:
            raise ValueError()
        return result

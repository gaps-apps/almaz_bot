from typing import Type, TypeVar
from aiohttp import ClientSession, BasicAuth
from pydantic import ValidationError

from lombardis.schemas import (
    ClientIDResponse,
    ClientDetailsResponse,
    ClientLoansResponse,
    LoanDetailsResponse,
)
from lombardis.dto import (
    ClientID,
    ClientDetails,
    ClientLoans,
    Loan,
    LoanDetails,
)
from config import conf  # Assuming conf is imported from a config module

T = TypeVar("T")

class LombardisAsyncHTTP:
    BASE_URL = conf["LOMBARDIS_URL"]
    AUTH = BasicAuth(conf["LOMBARDIS_USER"], conf["LOMBARDIS_PASSWORD"])

    async def make_request(
        self, api_method: str, request_data: dict[str, str], response_schema: Type[T]
    ) -> T:
        url = f"{self.BASE_URL}/{api_method}"
        async with ClientSession(auth=self.AUTH) as session:
            try:
                async with session.post(url, json=request_data) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return response_schema(**data)
            except ValidationError as e:
                raise ValueError(f"Response validation failed: {e}")
            except Exception as e:
                raise RuntimeError(f"Request to {api_method} failed: {e}")

    async def get_client_id(self, query_string: str) -> ClientID:
        response = await self.make_request(
            "getClientID", {"queryString": query_string}, ClientIDResponse
        )
        return ClientID(client_id=response.ClientID)

    async def get_client_details(self, client_id: str) -> ClientDetails:
        response = await self.make_request(
            "getClientDetails", {"clientID": client_id}, ClientDetailsResponse
        )
        return ClientDetails(
            full_name=f"{response.surname} {response.name} {response.patronymic or ''}".strip(),
            phone=response.phone,
        )

    async def get_client_loans(self, client_id: str) -> ClientLoans:
        response = await self.make_request(
            "getClientLoans", {"clientID": client_id}, ClientLoansResponse
        )
        return ClientLoans(
            loans=[
                Loan(loan.LoanID, loan.pawnBillNumber)
                for loan in response.Loans
            ]
        )

    async def get_loan_details(self, loan_id: str) -> LoanDetails:
        response = await self.make_request(
            "getLoanDetails", {"loanID": loan_id}, LoanDetailsResponse
        )
        return LoanDetails(
            loan_number=response.LoanNumber,
            loan_sum=response.LoanSum,
            interests_sum=response.InterestsSum,
            stuff=[item.Presentation for item in response.Stuff],
        )

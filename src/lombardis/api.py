from enum import Enum
from typing import Optional, Type, TypeVar

from aiohttp import BasicAuth, ClientSession
from pydantic import ValidationError

from config import conf  # Assuming conf is imported from a config module
from lombardis.dto import (ClientDetails, ClientID, ClientLoans, Loan,
                           LoanDetails)
from lombardis.schemas import (ClientDetailsResponse, ClientIDResponse,
                               ClientLoansResponse, LoanDetailsResponse)

T = TypeVar("T")


class HTTP_METHOD(Enum):
    GET = "get"
    PUT = "put"


class LombardisAsyncHTTP:
    def __init__(
        self,
        session: Optional[ClientSession] = None,
        base_url: str = conf["LOMBARDIS_URL"],
        auth: BasicAuth = BasicAuth(conf["LOMBARDIS_USER"], conf["LOMBARDIS_PASSWORD"]),
    ):
        self.BASE_URL = base_url
        self.AUTH = auth
        self.session = session or ClientSession(auth=self.AUTH)

    async def make_request(
        self,
        api_method: str,
        request_data: dict[str, str],
        response_schema: Type[T],
        http_method: HTTP_METHOD,
    ) -> T:
        url = f"{self.BASE_URL}/{api_method}"
        async with self.session as session:
            try:
                get_response = getattr(session, http_method.value)
                if get_response is None:
                    raise ValueError(f"Unsupported HTTP method: {http_method}")
                else:
                    async with get_response(url, json=request_data) as response:
                        response.raise_for_status()
                        data = await response.json()
                        return response_schema(**data)

            except ValidationError as e:
                raise ValueError(f"Response validation failed: {e}")
            except Exception as e:
                raise RuntimeError(f"Request to {api_method} failed: {e}")

    async def get_client_id(self, query_string: str) -> ClientID:
        response = await self.make_request(
            "getClientID",
            {"queryString": query_string},
            ClientIDResponse,
            HTTP_METHOD.PUT,
        )
        return ClientID(client_id=response.ClientID)

    async def get_client_details(self, client_id: str) -> ClientDetails:
        response = await self.make_request(
            "getClientDetails",
            {"clientID": client_id},
            ClientDetailsResponse,
            HTTP_METHOD.PUT,
        )
        return ClientDetails(
            full_name=f"{response.surname} {response.name} {response.patronymic or ''}".strip(),
            phone=response.phone,
        )

    async def get_client_loans(self, client_id: str) -> ClientLoans:
        response = await self.make_request(
            "getClientLoans",
            {"clientID": client_id},
            ClientLoansResponse,
            HTTP_METHOD.PUT,
        )
        return ClientLoans(
            loans=[Loan(loan.LoanID, loan.pawnBillNumber) for loan in response.Loans]
        )

    async def get_loan_details(self, loan_id: str) -> LoanDetails:
        response = await self.make_request(
            "getLoanDetails", {"loanID": loan_id}, LoanDetailsResponse, HTTP_METHOD.PUT
        )
        return LoanDetails(
            loan_number=response.LoanNumber,
            loan_sum=response.LoanSum,
            interests_sum=response.InterestsSum,
            stuff=[item.Presentation for item in response.Stuff],
        )

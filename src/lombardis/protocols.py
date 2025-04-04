from typing import Protocol

from lombardis.schemas import (ClientDetailsResponse, ClientLoansResponse,
                               LoanDetailsResponse)


class LombardisAPI(Protocol):
    async def get_client_loans(self, client_id: str) -> ClientLoansResponse | None: ...

    async def get_client_details(
        self, client_id: str
    ) -> ClientDetailsResponse | None: ...

    async def get_loan_details(self, loan_id: str) -> LoanDetailsResponse | None: ...

    async def get_client_id(self, query_string: str) -> str | None: ...

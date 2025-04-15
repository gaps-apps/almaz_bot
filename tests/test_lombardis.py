import sys
import os
from contextlib import asynccontextmanager
from polyfactory.factories import DataclassFactory
import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../deploy/.env")))

from lombardis.api import LombardisAsyncHTTP
from lombardis.dto import ClientID, ClientDetails, ClientLoans, LoanDetails, Loan
from lombardis.schemas import (
    ClientIDResponse,
    ClientDetailsResponse,
    ClientLoansResponse,
    LoanDetailsResponse,
)  # Use schemas from schemas.py


# Define factories for each schema
class ClientIDResponseFactory(DataclassFactory[ClientIDResponse]):
    __model__ = ClientIDResponse


class ClientDetailsResponseFactory(DataclassFactory[ClientDetailsResponse]):
    __model__ = ClientDetailsResponse


class ClientLoansResponseFactory(DataclassFactory[ClientLoansResponse]):
    __model__ = ClientLoansResponse


class LoanDetailsResponseFactory(DataclassFactory[LoanDetailsResponse]):
    __model__ = LoanDetailsResponse


def generate_api_response(factory):
    """Generate mock API response data using the provided factory."""
    return factory.build().__dict__


class ClientSessionMock:
    def __init__(self):
        self._responses = {}
        self._called_with = []

    def configure(self, method: str, url: str, response_data: dict, status: int = 200):
        self._responses[(method, url)] = (response_data, status)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @asynccontextmanager
    async def put(self, url, json=None):
        self._called_with.append(("PUT", url, json))
        if ("PUT", url) in self._responses:
            response_data, status = self._responses[("PUT", url)]
            yield MockResponse(response_data, status)
        else:
            raise RuntimeError(f"No mock configured for PUT {url}")

    @asynccontextmanager
    async def get(self, url, params=None):
        self._called_with.append(("GET", url, params))
        if ("GET", url) in self._responses:
            response_data, status = self._responses[("GET", url)]
            yield MockResponse(response_data, status)
        else:
            raise RuntimeError(f"No mock configured for GET {url}")

    def get_called_with(self):
        return self._called_with


class MockResponse:
    def __init__(self, json_data, status):
        self._json_data = json_data
        self._status = status

    async def json(self):
        return self._json_data

    def raise_for_status(self):
        if self._status >= 400:
            raise RuntimeError(f"HTTP Error: {self._status}")


@pytest.fixture
def mock_session() -> ClientSessionMock:
    return ClientSessionMock()


@pytest.fixture
def lombardis_client(mock_session: ClientSessionMock) -> LombardisAsyncHTTP:
    return LombardisAsyncHTTP(session=mock_session)


@pytest.mark.asyncio
async def test_get_client_id(
    lombardis_client: LombardisAsyncHTTP, mock_session: ClientSessionMock
) -> None:
    mock_data = generate_api_response(ClientIDResponseFactory)
    mock_session.configure("PUT", f"{lombardis_client.BASE_URL}/getClientID", mock_data)

    result = await lombardis_client.get_client_id("test_query")
    assert result == ClientID(client_id=mock_data["ClientID"])
    assert mock_session.get_called_with() == [
        (
            "PUT",
            f"{lombardis_client.BASE_URL}/getClientID",
            {"queryString": "test_query"},
        )
    ]


@pytest.mark.asyncio
async def test_get_client_details(
    lombardis_client: LombardisAsyncHTTP, mock_session: ClientSessionMock
) -> None:
    mock_data = generate_api_response(ClientDetailsResponseFactory)
    mock_session.configure(
        "PUT", f"{lombardis_client.BASE_URL}/getClientDetails", mock_data
    )

    result = await lombardis_client.get_client_details("12345")
    assert result == ClientDetails(
        full_name=f"{mock_data['surname']} {mock_data['name']} {mock_data['patronymic'] or ''}".strip(),
        phone=mock_data["phone"],
    )
    assert mock_session.get_called_with() == [
        ("PUT", f"{lombardis_client.BASE_URL}/getClientDetails", {"clientID": "12345"})
    ]


@pytest.mark.asyncio
async def test_get_client_loans(
    lombardis_client: LombardisAsyncHTTP, mock_session: ClientSessionMock
) -> None:
    mock_data = generate_api_response(ClientLoansResponseFactory)
    mock_session.configure(
        "PUT", f"{lombardis_client.BASE_URL}/getClientLoans", mock_data
    )

    result = await lombardis_client.get_client_loans("12345")
    assert result == ClientLoans(
        loans=[
            Loan(loan_id=loan.LoanID, pawn_bill_number=loan.pawnBillNumber)
            for loan in mock_data["Loans"]
        ]
    )
    assert mock_session.get_called_with() == [
        ("PUT", f"{lombardis_client.BASE_URL}/getClientLoans", {"clientID": "12345"})
    ]


@pytest.mark.asyncio
async def test_get_loan_details(
    lombardis_client: LombardisAsyncHTTP, mock_session: ClientSessionMock
) -> None:
    mock_data = generate_api_response(LoanDetailsResponseFactory)
    mock_session.configure(
        "PUT", f"{lombardis_client.BASE_URL}/getLoanDetails", mock_data
    )

    result = await lombardis_client.get_loan_details("1")
    assert result == LoanDetails(
        loan_number=mock_data["LoanNumber"],
        loan_sum=mock_data["LoanSum"],
        interests_sum=mock_data["InterestsSum"],
        stuff=[item.Presentation for item in mock_data["Stuff"]],
    )
    assert mock_session.get_called_with() == [
        ("PUT", f"{lombardis_client.BASE_URL}/getLoanDetails", {"loanID": "1"})
    ]

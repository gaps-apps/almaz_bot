import sys
import os
from typing import Generator
from contextlib import asynccontextmanager

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
# Load environment variables from the .env file in the deploy directory
from dotenv import load_dotenv # type: ignore
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../deploy/.env')))

import pytest # type: ignore
from lombardis.api import LombardisAsyncHTTP, HTTP_METHOD
from lombardis.dto import ClientID, ClientDetails, ClientLoans, LoanDetails, Loan

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
async def test_get_client_id(lombardis_client: LombardisAsyncHTTP, mock_session: ClientSessionMock) -> None:
    mock_session.configure(
        "PUT",
        f"{lombardis_client.BASE_URL}/getClientID",
        {"ClientID": "123e4567-e89b-12d3-a456-426614174000"}  # UUID format
    )

    result = await lombardis_client.get_client_id("test_query")
    assert result == ClientID(client_id="123e4567-e89b-12d3-a456-426614174000")
    assert mock_session.get_called_with() == [
        ("PUT", f"{lombardis_client.BASE_URL}/getClientID", {"queryString": "test_query"})
    ]

@pytest.mark.asyncio
async def test_get_client_details(lombardis_client: LombardisAsyncHTTP, mock_session: ClientSessionMock) -> None:
    mock_session.configure(
        "PUT",
        f"{lombardis_client.BASE_URL}/getClientDetails",
        {
            "taskStatus": 1,
            "dataToProcess": 1,
            "dataProcessed": 1,
            "dataDeclined": 0,
            "progress": 100.0,
            "isError": False,
            "startTime": "2023-01-01T00:00:00",
            "finishTime": "2023-01-01T01:00:00",
            "errorMessage": "",
            "providerID": "provider123",
            "taskID": "123e4567-e89b-12d3-a456-426614174000",
            "clientInternalCode": "internal123",
            "surname": "Doe",
            "name": "John",
            "patronymic": None,
            "email": None,
            "phone": "123456789",
            "taxNumber": None,
            "additionalInformation": [],
            "segments": []
        }
    )

    result = await lombardis_client.get_client_details("12345")
    assert result == ClientDetails(full_name="Doe John", phone="123456789")
    assert mock_session.get_called_with() == [
        ("PUT", f"{lombardis_client.BASE_URL}/getClientDetails", {"clientID": "12345"})
    ]

@pytest.mark.asyncio
async def test_get_client_loans(lombardis_client: LombardisAsyncHTTP, mock_session: ClientSessionMock) -> None:
    mock_session.configure(
        "PUT",
        f"{lombardis_client.BASE_URL}/getClientLoans",
        {
            "taskStatus": 1,
            "dataToProcess": 1,
            "dataProcessed": 1,
            "dataDeclined": 0,
            "progress": 100.0,
            "isError": False,
            "startTime": "2023-01-01T00:00:00",
            "finishTime": "2023-01-01T01:00:00",
            "errorMessage": "",
            "providerID": "provider123",
            "taskID": "123e4567-e89b-12d3-a456-426614174000",
            "Loans": [
                {
                    "LoanID": "123e4567-e89b-12d3-a456-426614174001",
                    "pawnBillNumber": "PB123",
                    "LoanDescription": "Loan Desc",
                    "ShortLoanDescription": "Short Desc",
                    "LoanDate": "2023-01-01T00:00:00",
                    "PaymentDate": "2023-01-15T00:00:00",
                    "Closed": False,
                    "fullDebt": 1000.0,
                    "prolongationSum": 100.0,
                    "sellingDate": None,
                    "PaymentAvailable": True
                }
            ]
        }
    )

    result = await lombardis_client.get_client_loans("12345")
    assert result == ClientLoans(loans=[Loan(loan_id="123e4567-e89b-12d3-a456-426614174001", pawn_bill_number="PB123")])
    assert mock_session.get_called_with() == [
        ("PUT", f"{lombardis_client.BASE_URL}/getClientLoans", {"clientID": "12345"})
    ]

@pytest.mark.asyncio
async def test_get_loan_details(lombardis_client: LombardisAsyncHTTP, mock_session: ClientSessionMock) -> None:
    mock_session.configure(
        "PUT",
        f"{lombardis_client.BASE_URL}/getLoanDetails",
        {
            "taskStatus": 1,
            "dataToProcess": 1,
            "dataProcessed": 1,
            "dataDeclined": 0,
            "progress": 100.0,
            "isError": False,
            "startTime": "2023-01-01T00:00:00",
            "finishTime": "2023-01-01T01:00:00",
            "errorMessage": "",
            "providerID": "provider123",
            "taskID": "123e4567-e89b-12d3-a456-426614174000",
            "LoanNumber": "LN123",
            "LoanDate": "2023-01-01T00:00:00",
            "PaymentDate": "2023-01-15T00:00:00",
            "SellingDate": None,
            "LoanSum": 1000.0,
            "DebtSum": 1050.0,
            "InterestsSum": 50.0,
            "Stuff": [
                {
                    "Presentation": "Gold Ring",
                    "Description": "A gold ring",
                    "FullDescription": "A beautiful gold ring",
                    "Status": "Available",
                    "Location": "Store 1",
                    "LocationID": "loc123",
                    "StuffID": "stuff123",
                    "Price": 500.0,
                    "BillNumber": "BN123",
                    "StuffCode": "SC123",
                    "Gems": None
                }
            ],
            "tariffID": "tariff123",
            "tariffDescription": None,
            "paymentAvailable": True
        }
    )

    result = await lombardis_client.get_loan_details("1")
    assert result == LoanDetails(
        loan_number="LN123",
        loan_sum=1000.0,
        interests_sum=50.0,
        stuff=["Gold Ring"]
    )
    assert mock_session.get_called_with() == [
        ("PUT", f"{lombardis_client.BASE_URL}/getLoanDetails", {"loanID": "1"})
    ]

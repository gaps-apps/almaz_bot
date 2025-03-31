import json

import aiohttp
from pydantic import ValidationError

from lombardis.schemas import (
    ClientListResponse,
    ClientLoansResponse,
    ClientDetailsResponse,
    Loan,
    LoanDetailsResponse,
)
from logger import logfire
from config import conf


class LombardisAPI:
    BASE_URL = conf["LOMBARDIS_URL"]

    def __init__(
        self,
        username: str = conf["LOMBARDIS_USER"],
        password: str = conf["LOMBARDIS_PASSWORD"],
    ):
        self.auth = aiohttp.BasicAuth(username, password)

    async def fetch_clients_list(self) -> ClientListResponse:
        with logfire.span("fetching clients list"):
            async with aiohttp.ClientSession(auth=self.auth) as session:
                try:
                    async with session.put(
                        self.BASE_URL + "getClientsList"
                    ) as response:
                        response.raise_for_status()
                        raw_data = await response.read()
                        json_data = json.loads(raw_data.decode("utf-8"))
                        try:
                            clients_resp = ClientListResponse(**json_data)
                            logfire.info(
                                f"success fetch clients count={len(clients_resp.ClientsList)}"
                            )
                            return clients_resp
                        except ValidationError as e:
                            logfire.exception(f"Validation Error: {e}")
                except aiohttp.ClientResponseError as e:
                    logfire.exception(f"HTTP Error: {e.status} - {e.message}")
                except aiohttp.ClientError as e:
                    logfire.exception(f"Request Error: {e}")
                except Exception as e:
                    logfire.exception(f"Unexpected Error: {e}")

    async def get_client_loans(self, client_id: str) -> ClientLoansResponse:
        with logfire.span(f"fetching client loans cliend_id={client_id}"):
            async with aiohttp.ClientSession(auth=self.auth) as session:
                try:
                    payload = json.dumps({"ClientID": client_id})
                    headers = {"Content-Type": "application/json"}
                    async with session.put(
                        self.BASE_URL + "getClientLoans", data=payload, headers=headers
                    ) as response:
                        response.raise_for_status()
                        raw_data = await response.read()
                        json_data = json.loads(raw_data.decode("utf-8"))
                        try:
                            loan_resp = ClientLoansResponse(**json_data)
                            logfire.info(
                                f"success fetch loans count={len(loan_resp.Loans)}"
                            )
                            return loan_resp
                        except ValidationError as e:
                            logfire.exception(f"Validation Error: {e}")
                except aiohttp.ClientResponseError as e:
                    logfire.exception(f"HTTP Error: {e.status} - {e.message}")
                except aiohttp.ClientError as e:
                    logfire.exception(f"Request Error: {e}")
                except Exception as e:
                    logfire.exception(f"Unexpected Error: {e}")

    async def get_client_details(self, client_id: str) -> ClientDetailsResponse:
        with logfire.span(f"fetching client details cliend_id={client_id}"):
            async with aiohttp.ClientSession(auth=self.auth) as session:
                try:
                    payload = json.dumps({"clientID": client_id})
                    headers = {"Content-Type": "application/json"}
                    async with session.put(
                        self.BASE_URL + "getClientDetails",
                        data=payload,
                        headers=headers,
                    ) as response:
                        response.raise_for_status()
                        raw_data = await response.read()
                        json_data = json.loads(raw_data.decode("utf-8"))
                        try:
                            client_details = ClientDetailsResponse(**json_data)
                            logfire.info(
                                f"success fetch client details client_id={client_id}"
                            )
                            return client_details
                        except ValidationError as e:
                            logfire.exception(f"Validation Error: {e}")
                except aiohttp.ClientResponseError as e:
                    logfire.exception(f"HTTP Error: {e.status} - {e.message}")
                except aiohttp.ClientError as e:
                    logfire.exception(f"Request Error: {e}")
                except Exception as e:
                    logfire.exception(f"Unexpected Error: {e}")

    async def get_loan_details(self, loan_id: str) -> LoanDetailsResponse:
        """Fetches loan details for a given loan ID."""
        with logfire.span(f"fetching loan details loan_id={loan_id}"):
            async with aiohttp.ClientSession(auth=self.auth) as session:
                try:
                    payload = json.dumps({"LoanID": loan_id})
                    headers = {"Content-Type": "application/json"}
                    async with session.put(
                        self.BASE_URL + "getLoanDetails", data=payload, headers=headers
                    ) as response:
                        response.raise_for_status()
                        raw_data = await response.read()
                        json_data = json.loads(raw_data.decode("utf-8"))
                        loan_details = LoanDetailsResponse(**json_data)
                        logfire.info(f"success fetch loan details loan_id={loan_id}")
                        return loan_details
                except ValidationError as e:
                    logfire.exception(f"Validation Error: {e}")
                except aiohttp.ClientResponseError as e:
                    logfire.exception(f"HTTP Error: {e.status} - {e.message}")
                except aiohttp.ClientError as e:
                    logfire.exception(f"Request Error: {e}")
                except Exception as e:
                    logfire.exception(f"Unexpected Error: {e}")
        return None

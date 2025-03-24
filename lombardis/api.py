import json

import aiohttp
from pydantic import ValidationError

from lombardis.dto import (
    ClientListResponse,
    ClientLoanResponse,
    ClientDetailsResponse,
)
from logger import logfire


class LombardisAPI:
    BASE_URL = "SKIPPED"

    def __init__(self, username: str, password: str):
        self.auth = aiohttp.BasicAuth(username, password)

    async def fetch_clients_list(self) -> ClientListResponse:
        with logfire.span("fetching clients list") as span:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                try:
                    async with session.put(
                        self.BASE_URL + "getClientsList"
                    ) as response:
                        response.raise_for_status()
                        raw_data = await response.read()
                        json_data = json.loads(raw_data.decode("utf-8"))
                        try:
                            return ClientListResponse(**json_data)
                        except ValidationError:
                            logfire.exception(f"Validation Error: {e}")
                except aiohttp.ClientResponseError as e:
                    logfire.exception(f"HTTP Error: {e.status} - {e.message}")
                except aiohttp.ClientError as e:
                    logfire.exception(f"Request Error: {e}")
                except Exception as e:
                    logfire.exception(f"Unexpected Error: {e}")

    async def get_client_loans(self, client_id: str) -> ClientLoanResponse:
        with logfire.span("fetching client loans") as span:
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
                            return ClientLoanResponse(**json_data)
                        except ValidationError as e:
                            logfire.exception(f"Validation Error: {e}")
                except aiohttp.ClientResponseError as e:
                    logfire.exception(f"HTTP Error: {e.status} - {e.message}")
                except aiohttp.ClientError as e:
                    logfire.exception(f"Request Error: {e}")
                except Exception as e:
                    logfire.exception(f"Unexpected Error: {e}")

    async def get_client_details(self, client_id: str) -> ClientDetailsResponse:
        with logfire.span("fetching client details") as span:
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
                            return ClientDetailsResponse(**json_data)
                        except ValidationError as e:
                            logfire.exception(f"Validation Error: {e}")
                except aiohttp.ClientResponseError as e:
                    logfire.exception(f"HTTP Error: {e.status} - {e.message}")
                except aiohttp.ClientError as e:
                    logfire.exception(f"Request Error: {e}")
                except Exception as e:
                    logfire.exception(f"Unexpected Error: {e}")

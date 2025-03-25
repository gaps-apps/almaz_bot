from typing import Optional

import aiosqlite

from lombardis.api import LombardisAPI
from logger import logfire
from config import conf

from .dto import ClientBasicInfoDTO


async def fetch_and_update_local_db(db_path: str = "lombardis.db"):
    with logfire.span("fetching and storing clients"):
        client_list_response = await LombardisAPI().fetch_clients_list()
        if not client_list_response or not client_list_response.ClientsList:
            logfire.warning("No clients retrieved from API.")
            return

        async with aiosqlite.connect(db_path) as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    clientID TEXT PRIMARY KEY,
                    phone TEXT,
                    fullDebt REAL,
                    fullInterestsDebt REAL,
                    overdueDebt REAL,
                    overdueInterestsDebt REAL,
                    nearestPaymentDate TEXT
                )
                """
            )

            for client in client_list_response.ClientsList:
                await conn.execute(
                    """
                    INSERT INTO clients (clientID, phone, fullDebt, fullInterestsDebt, overdueDebt, overdueInterestsDebt, nearestPaymentDate)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(clientID) DO UPDATE SET
                        phone=excluded.phone,
                        fullDebt=excluded.fullDebt,
                        fullInterestsDebt=excluded.fullInterestsDebt,
                        overdueDebt=excluded.overdueDebt,
                        overdueInterestsDebt=excluded.overdueInterestsDebt,
                        nearestPaymentDate=excluded.nearestPaymentDate
                    """,
                    (
                        str(client.ClientID),
                        client.PhoneNumber,
                        client.FullDebt,
                        client.FullInterestsDebt,
                        client.OverdueDebt,
                        client.OverdueInterestsDebt,
                        (
                            client.NearestPaymentDate.isoformat()
                            if client.NearestPaymentDate
                            else None
                        ),
                    ),
                )

            await conn.commit()
            logfire.info(
                f"Client list successfully stored in the database. Count: {len(client_list_response.ClientsList)}"
            )


async def get_client_id_by_phone(phone: str, db_path: str = "lombardis.db"):
    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(
            "SELECT clientID FROM clients WHERE phone = ?", (phone,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def get_client_info_by_id(
    client_id: str, db_path: str = "lombardis.db"
) -> Optional[ClientBasicInfoDTO]:
    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(
            """
            SELECT clientID, phone, fullDebt, fullInterestsDebt, overdueDebt, overdueInterestsDebt, nearestPaymentDate
            FROM clients
            WHERE clientID = ?
            """,
            (client_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return ClientBasicInfoDTO(*row)
            return None


async def get_client_info_by_phone(
    phone: str, db_path: str = "lombardis.db"
) -> Optional[ClientBasicInfoDTO]:
    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(
            """
            SELECT clientID, phone, fullDebt, fullInterestsDebt, overdueDebt, overdueInterestsDebt, nearestPaymentDate
            FROM clients
            WHERE phone = ?
            """,
            (phone,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return ClientBasicInfoDTO(*row)
            return None

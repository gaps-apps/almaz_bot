from typing import Optional, Dict

import aiosqlite

from lombardis.api import LombardisAPI
from logger import logfire

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
                    client_id TEXT PRIMARY KEY,
                    phone_number TEXT,
                    full_debt REAL,
                    full_interest_debt REAL,
                    overdue_debt REAL,
                    overdue_interest_debt REAL,
                    nearest_payment_date TEXT
                )
                """
            )

            for client in client_list_response.ClientsList:
                await conn.execute(
                    """
                    INSERT INTO clients (client_id, phone_number, full_debt, full_interest_debt, overdue_debt, overdue_interest_debt, nearest_payment_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(client_id) DO UPDATE SET
                        phone_number=excluded.phone_number,
                        full_debt=excluded.full_debt,
                        full_interest_debt=excluded.full_interest_debt,
                        overdue_debt=excluded.overdue_debt,
                        overdue_interest_debt=excluded.overdue_interest_debt,
                        nearest_payment_date=excluded.nearest_payment_date
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


async def get_client_id_by_phone(phone_number: str, db_path: str = "lombardis.db"):
    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(
            "SELECT client_id FROM clients WHERE phone_number = ?", (phone_number,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def get_basic_info_by_params(
    params: Dict[str, str], db_path: str = "lombardis.db"
) -> Optional[ClientBasicInfoDTO]:
    if not params:
        return None

    query = "SELECT client_id, phone_number, full_debt, full_interest_debt, overdue_debt, overdue_interest_debt, nearest_payment_date FROM clients"
    conditions = []
    values = []

    for key, value in params.items():
        conditions.append(f"{key} = ?")
        values.append(value)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    async with aiosqlite.connect(db_path) as conn:
        async with conn.execute(query, values) as cursor:
            row = await cursor.fetchone()
            if row:
                return ClientBasicInfoDTO(*row)
            return None

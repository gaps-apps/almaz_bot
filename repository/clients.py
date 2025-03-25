import aiosqlite

from lombardis.api import LombardisAPI
from logger import logfire


async def fetch_and_store_clients(api: LombardisAPI, db_path: str = "lombardis.db"):
    with logfire.span("fetching and storing clients") as span:
        client_list_response = await api.fetch_clients_list()
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


# TODO get client id by phone

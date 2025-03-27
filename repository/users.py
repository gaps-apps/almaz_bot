import aiosqlite
from typing import Optional

from config import conf

from .dto import UserDTO


async def create_users_table(db_name=conf["USERS_DB"]):
    """Creates an SQLite table with chat_id, full_name, and clientID using aiosqlite."""
    async with aiosqlite.connect(db_name) as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                client_id TEXT NOT NULL UNIQUE,
                phone_number TEXT NOT NULL UNIQUE
            )
            """
        )
        await connection.commit()


async def user_exists(chat_id: int, db_name=conf["USERS_DB"]) -> bool:
    """Checks if a user with the given chat_id exists in the database."""
    async with aiosqlite.connect(db_name) as connection:
        async with connection.execute(
            "SELECT 1 FROM users WHERE chat_id = ?", (chat_id,)
        ) as cursor:
            return await cursor.fetchone() is not None


async def add_user(
    chat_id: int,
    full_name: str,
    client_id: str,
    phone_number: str,
    db_name=conf["USERS_DB"],
) -> Optional[UserDTO]:
    """Adds a new user to the database."""
    async with aiosqlite.connect(db_name) as connection:
        await connection.execute(
            """
            INSERT INTO users (chat_id, full_name, client_id, phone_number)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, full_name, client_id, phone_number),
        )
        await connection.commit()
        return UserDTO(chat_id, full_name, client_id, phone_number)


async def get_user_by_params(
    params: dict, db_name=conf["USERS_DB"]
) -> Optional[UserDTO]:
    """Fetches a user by given parameters."""
    if not params:
        raise ValueError("At least one parameter must be provided.")

    conditions = " AND ".join([f"{key} = ?" for key in params.keys()])
    values = tuple(params.values())
    query = f"SELECT chat_id, full_name, client_id, phone_number FROM users WHERE {conditions}"

    async with aiosqlite.connect(db_name) as connection:
        async with connection.execute(query, values) as cursor:
            row = await cursor.fetchone()
            if row:
                return UserDTO(
                    chat_id=row[0],
                    full_name=row[1],
                    client_id=row[2],
                    phone_number=row[3],
                )
            return None

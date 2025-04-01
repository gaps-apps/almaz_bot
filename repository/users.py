from typing import Dict, Optional

import aiosqlite

from config import conf

from .dto import UserDTO


class UsersRepo:
    """Repository class for managing user-related database operations."""

    def __init__(self, db_name: str = conf["USERS_DB"]):
        self.db_name = db_name
        self.connection = None

    async def connect(self):
        """Establishes a shared database connection."""
        if self.connection is None:
            self.connection = await aiosqlite.connect(self.db_name)

    async def close(self):
        """Closes the shared database connection."""
        if self.connection:
            await self.connection.close()
            self.connection = None

    async def bootstrap(self):
        """Creates the users table if it does not exist."""
        await self.connect()
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                client_id TEXT NOT NULL UNIQUE,
                phone_number TEXT NOT NULL UNIQUE
            )
            """
        )
        await self.connection.commit()

    async def user_exists(self, chat_id: int) -> bool:
        """Checks if a user with the given chat_id exists in the database."""
        await self.connect()
        async with self.connection.execute(
            "SELECT 1 FROM users WHERE chat_id = ?", (chat_id,)
        ) as cursor:
            return await cursor.fetchone() is not None

    async def add_user(self, user: UserDTO) -> Optional[UserDTO]:
        """Adds a new user to the database."""
        await self.connect()
        await self.connection.execute(
            """
            INSERT INTO users (chat_id, full_name, client_id, phone_number)
            VALUES (?, ?, ?, ?)
            """,
            (user.chat_id, user.full_name, user.client_id, user.phone_number),
        )
        await self.connection.commit()
        return user

    async def get_user_by_params(self, params: Dict[str, str]) -> Optional[UserDTO]:
        """Fetches a user by given parameters."""
        if not params:
            raise ValueError("At least one parameter must be provided.")

        await self.connect()
        conditions = " AND ".join([f"{key} = ?" for key in params.keys()])
        values = tuple(params.values())
        query = f"SELECT chat_id, full_name, client_id, phone_number FROM users WHERE {conditions}"

        async with self.connection.execute(query, values) as cursor:
            row = await cursor.fetchone()
            if row:
                return UserDTO(
                    chat_id=row[0],
                    full_name=row[1],
                    client_id=row[2],
                    phone_number=row[3],
                )
            return None

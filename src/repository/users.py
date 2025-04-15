from typing import Any, Dict, Optional

import aiosqlite

from config import conf

from .dto import User


class UsersRepoSQLite:
    def __init__(self, db_name: str = conf["USERS_DB"]):
        self.db_name = db_name
        self.connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        if self.connection is None:
            try:
                self.connection = await aiosqlite.connect(self.db_name)
            except Exception as e:
                raise RuntimeError(f"Failed to connect to sqlite database: {e}")

    async def close(self) -> None:
        if self.connection:
            try:
                await self.connection.close()
                self.connection = None
            except Exception as e:
                raise RuntimeError(f"Failed to close sqlite database connection: {e}")

    async def bootstrap(self) -> None:
        try:
            await self.connect()
            assert self.connection is not None
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
        except Exception as e:
            raise RuntimeError(f"Failed to bootstrap sqlite database tables: {e}")

    async def user_exists(self, chat_id: int) -> bool:
        try:
            await self.connect()
            assert self.connection is not None
            async with self.connection.execute(
                "SELECT 1 FROM users WHERE chat_id = ?", (chat_id,)
            ) as cursor:
                return await cursor.fetchone() is not None
        except Exception as e:
            raise RuntimeError(f"Failed to check user existence: {e}")

    async def add_user(self, user: User) -> None:
        try:
            await self.connect()
            assert self.connection is not None
            await self.connection.execute(
                """
                INSERT INTO users (chat_id, full_name, client_id, phone_number)
                VALUES (?, ?, ?, ?)
                """,
                (user.chat_id, user.full_name, user.client_id, user.phone_number),
            )
            await self.connection.commit()
        except Exception as e:
            raise RuntimeError(f"Failed to add user to sqlite database: {e}")

    async def get_user(self, params: Dict[str, Any]) -> Optional[User]:
        if not params:
            raise ValueError("At least one parameter must be provided.")

        try:
            await self.connect()
            assert self.connection is not None
            conditions = " AND ".join([f"{key} = ?" for key in params.keys()])
            values = tuple(params.values())
            query = f"SELECT chat_id, full_name, client_id, phone_number FROM users WHERE {conditions}"

            async with self.connection.execute(query, values) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        chat_id=row[0],
                        full_name=row[1],
                        client_id=row[2],
                        phone_number=row[3],
                    )
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to fetch user from sqlite database: {e}")

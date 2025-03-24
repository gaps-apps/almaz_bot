import aiosqlite


async def create_users_table(db_name="users.db"):
    """Creates an SQLite table with chat_id, full_name, and clientID using aiosqlite."""
    async with aiosqlite.connect(db_name) as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                clientID TEXT NOT NULL UNIQUE
            )
        """
        )
        await connection.commit()


async def user_exists(chat_id: int, db_name="users.db") -> bool:
    """Checks if a user with the given chat_id exists in the database."""
    async with aiosqlite.connect(db_name) as connection:
        async with connection.execute(
            "SELECT 1 FROM users WHERE chat_id = ?", (chat_id,)
        ) as cursor:
            return await cursor.fetchone() is not None


async def add_user(
    chat_id: int, full_name: str, clientID: str, db_name="users.db"
) -> None:
    """Adds a new user to the database."""
    async with aiosqlite.connect(db_name) as connection:
        await connection.execute(
            """
            INSERT INTO users (chat_id, full_name, clientID)
            VALUES (?, ?, ?)
            """,
            (chat_id, full_name, clientID),
        )
        await connection.commit()

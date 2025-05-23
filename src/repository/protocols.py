from typing import Any, Dict, Optional, Protocol

from .dto import User


class UsersRepo(Protocol):
    """Protocol for User Repositories defining expected methods."""

    async def connect(self) -> None: ...

    async def close(self) -> None: ...

    async def bootstrap(self) -> None: ...

    async def user_exists(self, chat_id: int) -> bool: ...

    async def add_user(self, user: User) -> None: ...

    async def get_user(self, params: Dict[str, Any]) -> Optional[User]: ...

import os
from typing import TypedDict, cast


class Config(TypedDict):
    POLLING: str
    ADMIN_SECRET: str
    LF_TOKEN: str
    BOT_TOKEN: str
    WEBHOOK_BASE: str
    WEB_SERVER_HOST: str
    WEB_SERVER_PORT: str
    LOMBARDIS_USER: str
    LOMBARDIS_PASSWORD: str
    USERS_DB: str
    LOMBARDIS_DB: str
    LOMBARDIS_URL: str


def get_from_env() -> Config:
    try:
        return cast(
            Config, {var: os.environ[var] for var in Config.__annotations__}
        )  # Ensures values are non-None
    except KeyError:
        exit(1)

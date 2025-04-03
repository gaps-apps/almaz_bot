from .load import Config, get_from_env

conf: Config = get_from_env()

__all__ = ["conf", "Config"]

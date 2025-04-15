import logfire
from logging import basicConfig

from config import conf

logfire.configure(token=conf["LF_TOKEN"])
logfire.instrument_pydantic(record="failure")

basicConfig(handlers=[logfire.LogfireLoggingHandler()])

__all__ = ["logfire"]

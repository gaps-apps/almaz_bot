import logfire

from config import conf

logfire.configure(token=conf["LF_TOKEN"])
logfire.instrument_pydantic(record="failure")

__all__ = ["logfire"]

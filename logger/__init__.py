import logfire

logfire.configure(token="SKIPPED")
logfire.instrument_pydantic()
logfire.instrument_aiohttp_client()

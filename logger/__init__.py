import logfire

logfire.configure(token="SKIPPED")
logfire.instrument_pydantic(record="failure")
logfire.instrument_aiohttp_client()

import asyncio

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

from app.request_limits import RequestBodyLimitMiddleware


@pytest.mark.parametrize("chunked", [False, True], ids=["fixed-length", "streamed"])
def test_request_body_limit_applies_before_the_handler(chunked):
    async def run_test():
        app = FastAPI()
        app.add_middleware(RequestBodyLimitMiddleware, max_bytes=8)
        received = []

        @app.post("/")
        async def record_body(request: Request):
            body = await request.body()
            received.append(body)
            return {"size": len(body)}

        async def chunks(content):
            yield content[:4]
            yield content[4:]

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            accepted_body = b"12345678"
            rejected_body = b"123456789"
            allowed = await client.post(
                "/", content=chunks(accepted_body) if chunked else accepted_body
            )
            assert allowed.status_code == 200, allowed.text
            assert allowed.json() == {"size": 8}
            rejected = await client.post(
                "/", content=chunks(rejected_body) if chunked else rejected_body
            )
            assert rejected.status_code == 413, rejected.text
            assert received == [accepted_body]

    asyncio.run(run_test())

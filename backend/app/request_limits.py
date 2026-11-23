from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_REQUEST_BODY_BYTES = 8 * 1024 * 1024


class RequestBodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = MAX_REQUEST_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        try:
            declared_size = int(headers.get("content-length", "0"))
            if declared_size < 0:
                raise ValueError
        except ValueError:
            await JSONResponse(
                {"detail": "Invalid Content-Length header."}, status_code=400
            )(scope, receive, send)
            return

        too_large = JSONResponse(
            {"detail": f"Request body exceeds the {self.max_bytes}-byte limit."},
            status_code=413,
        )
        if declared_size > self.max_bytes:
            await too_large(scope, receive, send)
            return

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.max_bytes:
                await too_large(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        buffered_body: bytes | None = bytes(body)
        del body

        async def replay_body() -> Message:
            nonlocal buffered_body
            if buffered_body is None:
                return await receive()
            message = {
                "type": "http.request",
                "body": buffered_body,
                "more_body": False,
            }
            buffered_body = None
            return message

        await self.app(scope, replay_body, send)

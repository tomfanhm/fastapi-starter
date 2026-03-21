from __future__ import annotations

import time
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class TimingMiddleware:
    """Pure ASGI middleware that adds X-Process-Time header to every response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                process_time = time.perf_counter() - start_time
                headers: list[Any] = list(message.get("headers", []))
                headers.append((b"x-process-time", f"{process_time:.4f}".encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

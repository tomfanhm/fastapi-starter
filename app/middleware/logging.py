from __future__ import annotations

import logging
import time
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("app.middleware.logging")


class LoggingMiddleware:
    """Pure ASGI middleware that logs request method, path, client IP, status code, and process time."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        method: str = scope.get("method", "")
        path: str = scope.get("path", "")
        client: Any = scope.get("client")
        client_ip: str = client[0] if client else "unknown"

        status_code = 0

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        await self.app(scope, receive, send_wrapper)

        process_time_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "%s %s from %s -> %d (%.1fms)",
            method,
            path,
            client_ip,
            status_code,
            process_time_ms,
        )

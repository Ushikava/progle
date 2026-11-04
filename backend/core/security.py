import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from core.exceptions import TooManyRequestsError
from core.settings import TRUSTED_ORIGINS

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


def _is_cross_site(request: Request) -> bool:
    origin = request.headers.get("origin")
    if origin is not None:
        return origin not in TRUSTED_ORIGINS
    return request.headers.get("sec-fetch-site") == "cross-site"


async def security_middleware(request: Request, call_next):
    if request.method in UNSAFE_METHODS and _is_cross_site(request):
        response = JSONResponse(status_code=403, content={"detail": "Запрос с чужого сайта отклонён"})
    else:
        response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


class RateLimiter:
    MAX_TRACKED_CLIENTS = 10_000

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, request: Request) -> None:
        now = time.monotonic()
        if len(self.hits) > self.MAX_TRACKED_CLIENTS:
            self._forget_idle_clients(now)

        client = request.client.host if request.client else "unknown"
        hits = self.hits[client]
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()
        if len(hits) >= self.max_requests:
            raise TooManyRequestsError("Слишком много запросов, подождите минуту")
        hits.append(now)

    def _forget_idle_clients(self, now: float) -> None:
        idle = [c for c, h in self.hits.items() if not h or now - h[-1] > self.window_seconds]
        for client in idle:
            del self.hits[client]

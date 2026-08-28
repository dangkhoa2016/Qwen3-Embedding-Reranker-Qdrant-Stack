from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager


class QueueFullError(RuntimeError):
    pass


class InferenceGate:
    def __init__(self, max_concurrency: int = 1, max_waiters: int = 32):
        if max_concurrency != 1:
            raise ValueError("v0.1.0 requires max_concurrency=1 for CPU memory safety")
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._state_lock = asyncio.Lock()
        self._active = 0
        self._waiters = 0
        self._max_waiters = max_waiters

    @asynccontextmanager
    async def slot(self):
        queued = False
        async with self._state_lock:
            if self._active >= 1 or self._semaphore.locked():
                if self._waiters >= self._max_waiters:
                    raise QueueFullError("inference queue is full")
                self._waiters += 1
                queued = True
        started_wait = time.perf_counter()
        try:
            await self._semaphore.acquire()
        finally:
            if queued:
                async with self._state_lock:
                    self._waiters -= 1
        queue_wait_ms = (time.perf_counter() - started_wait) * 1000.0
        async with self._state_lock:
            self._active += 1
        try:
            yield round(queue_wait_ms, 3)
        finally:
            async with self._state_lock:
                self._active -= 1
            self._semaphore.release()

    def snapshot(self) -> dict[str, int]:
        return {"active": self._active, "waiters": self._waiters, "max_waiters": self._max_waiters}

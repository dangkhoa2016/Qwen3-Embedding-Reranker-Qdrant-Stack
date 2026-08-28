from __future__ import annotations

import fcntl
from pathlib import Path
from typing import TextIO


class ProcessSingletonLockError(RuntimeError):
    pass


class ProcessSingletonLock:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._handle: TextIO | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            handle.close()
            raise ProcessSingletonLockError(
                f"another model-host process already holds {self.path}; use exactly one Uvicorn worker"
            ) from exc
        handle.seek(0)
        handle.truncate()
        import os
        handle.write(f"pid={os.getpid()}\n")
        handle.flush()
        self._handle = handle

    def release(self) -> None:
        if self._handle is None:
            return
        try:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()

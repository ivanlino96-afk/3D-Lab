from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Protocol, TypeVar

T = TypeVar("T")


class UnitOfWork(Protocol):
    def __enter__(self) -> UnitOfWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class PrivateStorage(Protocol):
    def save(self, key: str, chunks: Iterable[bytes]) -> int: ...

    def open(self, key: str) -> AbstractContextManager[object]: ...

    def delete(self, key: str) -> bool: ...

    def path_for(self, key: str) -> Path: ...


class EmailGateway(Protocol):
    def send(self, recipient: str, subject: str, body: str) -> None: ...

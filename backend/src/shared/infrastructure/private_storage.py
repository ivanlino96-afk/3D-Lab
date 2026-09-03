from __future__ import annotations

import re
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

SAFE_KEY = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9/_-]{0,199}$")


class FileSystemPrivateStorage:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def path_for(self, key: str) -> Path:
        if not SAFE_KEY.fullmatch(key) or ".." in key.split("/"):
            raise ValueError("La clave de almacenamiento no es válida.")
        target = (self._root / key).resolve()
        if self._root not in target.parents:
            raise ValueError("La clave de almacenamiento sale del área privada.")
        return target

    def save(self, key: str, chunks: Iterable[bytes]) -> int:
        target = self.path_for(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".part")
        size = 0
        try:
            with temporary.open("wb") as stream:
                for chunk in chunks:
                    if not chunk:
                        continue
                    stream.write(chunk)
                    size += len(chunk)
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return size

    @contextmanager
    def open(self, key: str) -> Iterable[BinaryIO]:
        with self.path_for(key).open("rb") as stream:
            yield stream

    def delete(self, key: str) -> bool:
        target = self.path_for(key)
        if not target.exists():
            return False
        target.unlink()
        return True
